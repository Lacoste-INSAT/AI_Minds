"""
Query Planner
=============
Classifies user queries into types to determine retrieval strategy.

Query Types:
- SIMPLE: Direct factual question → dense vector search
- MULTI_HOP: Connects multiple entities → graph traversal + vector
- TEMPORAL: Time-based evolution → belief timeline query
- CONTRADICTION: Checking for conflicting info → belief diff

This is a critical component for routing queries to the right retrieval path.
"""

import structlog
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import json
import re

from .ollama_client import OllamaClient, ModelTier

logger = structlog.get_logger(__name__)


class QueryType(Enum):
    """Types of queries with different retrieval strategies."""
    SIMPLE = "simple"           # "What is X?" → dense search
    MULTI_HOP = "multi_hop"     # "Ideas from Y about X" → graph + vector
    TEMPORAL = "temporal"       # "How did my view on X change?" → timeline
    CONTRADICTION = "contradiction"  # "Did I say conflicting things?" → belief diff
    AGGREGATION = "aggregation" # "What are my priorities?" → multi-doc summary


@dataclass
class QueryPlan:
    """Plan for how to process a query."""
    query_type: QueryType
    original_query: str
    entities_mentioned: list[str]
    time_range: Optional[str]  # e.g., "this week", "last month"
    requires_graph: bool
    requires_temporal: bool
    reasoning: str  # Why this classification
    

# Keywords that suggest query types (fast regex-based pre-classification)
TEMPORAL_KEYWORDS = [
    r'\bover time\b', r'\bchanged?\b', r'\bevolved?\b', r'\bhistory\b',
    r'\bprogress\b', r'\bwhen did\b', r'\blast (week|month|year)\b',
    r'\bthis (week|month|year)\b', r'\brecently\b', r'\bbefore\b', r'\bafter\b',
    r'\btimeline\b', r'\btrend\b', r'\bshift\b'
]

MULTI_HOP_KEYWORDS = [
    r'\babout\b.*\babout\b', r'\bconnect(ed|ion)?\b', r'\brelat(ed|ion|e|es)\b',
    r'\bbetween\b', r'\blink\b', r'\bfrom\b.*\babout\b', 
    r'\bwhat did .+ say about\b', r'\bhow does .+ relate\b',
    r'\bsay about\b', r'\bsaid about\b'
]

CONTRADICTION_KEYWORDS = [
    r'\bconflict\b', r'\bcontradict\b', r'\binconsisten\b', r'\bdisagree\b',
    r'\bdifferent views?\b', r'\bchanged (my|their) mind\b'
]

AGGREGATION_KEYWORDS = [
    r'\ball\b', r'\bsummar(y|ize)\b', r'\bpriorities\b', r'\btop\b',
    r'\bmost (important|frequent|common)\b', r'\boverall\b', r'\bhow many\b',
    r'\blist\b', r'\beverything\b'
]


QUERY_PLANNER_SYSTEM_PROMPT = """You are a query classification agent for a personal knowledge system.

Your job: Classify the user's question into ONE category and extract entities mentioned.

Categories:
- SIMPLE: Direct factual question about one topic. "What is the marketing budget?" "Who is Sarah?"
- MULTI_HOP: Connects multiple entities or requires traversing relationships. "What did Sarah say about the marketing budget?" "How does Project X relate to the Q3 goals?"
- TEMPORAL: About change over time, evolution of thinking, historical comparison. "How has my view on pricing changed?" "What did I decide last month vs now?"
- CONTRADICTION: Looking for conflicting information or inconsistencies. "Did I say different things about the launch date?" "Are there contradictions in my notes?"
- AGGREGATION: Summarizing across multiple documents or counting. "What are my top priorities?" "Summarize everything about the product launch."

Output JSON ONLY (no other text):
{
    "query_type": "SIMPLE|MULTI_HOP|TEMPORAL|CONTRADICTION|AGGREGATION",
    "entities": ["entity1", "entity2"],
    "time_range": "this week|last month|null",
    "reasoning": "Brief explanation why this classification"
}"""


class QueryPlanner:
    """
    Classifies queries to determine optimal retrieval strategy.
    
    Uses a two-stage approach:
    1. Fast regex-based heuristics for obvious cases
    2. LLM classification for ambiguous queries
    
    This ensures fast response for simple queries while handling complex ones accurately.
    """
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
        self._compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> dict[QueryType, list[re.Pattern]]:
        """Pre-compile regex patterns for fast matching."""
        return {
            QueryType.TEMPORAL: [re.compile(p, re.IGNORECASE) for p in TEMPORAL_KEYWORDS],
            QueryType.MULTI_HOP: [re.compile(p, re.IGNORECASE) for p in MULTI_HOP_KEYWORDS],
            QueryType.CONTRADICTION: [re.compile(p, re.IGNORECASE) for p in CONTRADICTION_KEYWORDS],
            QueryType.AGGREGATION: [re.compile(p, re.IGNORECASE) for p in AGGREGATION_KEYWORDS],
        }
    
    def _quick_classify(self, query: str) -> Optional[QueryType]:
        """
        Fast regex-based classification.
        Returns None if no clear match (needs LLM).
        """
        scores = {}
        
        for query_type, patterns in self._compiled_patterns.items():
            matches = sum(1 for p in patterns if p.search(query))
            if matches > 0:
                scores[query_type] = matches
        
        if not scores:
            return None
        
        # If clear winner (2+ matches), use it
        max_score = max(scores.values())
        if max_score >= 2:
            winners = [qt for qt, score in scores.items() if score == max_score]
            if len(winners) == 1:
                return winners[0]
        
        # Ambiguous - needs LLM
        return None
    
    def _extract_entities_regex(self, query: str) -> list[str]:
        """
        Extract potential entity names using simple heuristics.
        Looks for capitalized words, quoted strings, etc.
        """
        entities = []
        
        # Quoted strings
        quoted = re.findall(r'"([^"]+)"', query)
        entities.extend(quoted)
        
        # Capitalized words (likely names/projects)
        # Exclude common sentence starters
        capitals = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', query)
        skip_words = {'What', 'Who', 'Where', 'When', 'Why', 'How', 'Did', 'Does', 
                      'Is', 'Are', 'Can', 'Could', 'Would', 'Should', 'The', 'This', 
                      'That', 'My', 'Your', 'Our', 'Their', 'I'}
        for cap in capitals:
            if cap not in skip_words and cap not in entities:
                entities.append(cap)
        
        return entities
    
    async def plan(self, query: str, use_llm: bool = True) -> QueryPlan:
        """
        Create an execution plan for the query.
        
        Args:
            query: User's question
            use_llm: Whether to use LLM for classification (set False for testing)
            
        Returns:
            QueryPlan with type, entities, and retrieval instructions
        """
        # Stage 1: Fast regex classification
        quick_type = self._quick_classify(query)
        quick_entities = self._extract_entities_regex(query)
        
        # Check for time range in query
        time_patterns = {
            r'\bthis week\b': 'this week',
            r'\blast week\b': 'last week',
            r'\bthis month\b': 'this month',
            r'\blast month\b': 'last month',
            r'\btoday\b': 'today',
            r'\byesterday\b': 'yesterday',
        }
        time_range = None
        for pattern, label in time_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                time_range = label
                break
        
        # If quick classification is confident, use it
        if quick_type and len(quick_entities) > 0:
            logger.info(
                "query_classified_fast",
                query_type=quick_type.value,
                entities=quick_entities
            )
            return QueryPlan(
                query_type=quick_type,
                original_query=query,
                entities_mentioned=quick_entities,
                time_range=time_range,
                requires_graph=quick_type in [QueryType.MULTI_HOP, QueryType.CONTRADICTION],
                requires_temporal=quick_type == QueryType.TEMPORAL,
                reasoning="Classified via keyword matching"
            )
        
        # Stage 2: LLM classification for ambiguous queries
        if use_llm:
            try:
                llm_plan = await self._llm_classify(query)
                if llm_plan:
                    return llm_plan
            except Exception as e:
                logger.warning("llm_classification_failed", error=str(e))
        
        # Fallback: Default to SIMPLE with extracted entities
        fallback_type = quick_type or QueryType.SIMPLE
        return QueryPlan(
            query_type=fallback_type,
            original_query=query,
            entities_mentioned=quick_entities,
            time_range=time_range,
            requires_graph=False,
            requires_temporal=False,
            reasoning="Fallback classification (LLM unavailable or no clear pattern)"
        )
    
    async def _llm_classify(self, query: str) -> Optional[QueryPlan]:
        """Use LLM for query classification."""
        try:
            response = await self.ollama.generate(
                prompt=f"Classify this query: {query}",
                system_prompt=QUERY_PLANNER_SYSTEM_PROMPT,
                temperature=0.0,  # Deterministic
                max_tokens=256,
                json_mode=True,
            )
            
            # Parse JSON response
            result = json.loads(response.content)
            
            # Map string to enum
            type_map = {
                "SIMPLE": QueryType.SIMPLE,
                "MULTI_HOP": QueryType.MULTI_HOP,
                "TEMPORAL": QueryType.TEMPORAL,
                "CONTRADICTION": QueryType.CONTRADICTION,
                "AGGREGATION": QueryType.AGGREGATION,
            }
            
            query_type = type_map.get(result.get("query_type", "").upper(), QueryType.SIMPLE)
            entities = result.get("entities", [])
            time_range = result.get("time_range")
            if time_range == "null" or not time_range:
                time_range = None
            reasoning = result.get("reasoning", "LLM classification")
            
            logger.info(
                "query_classified_llm",
                query_type=query_type.value,
                entities=entities,
                model=response.model_used
            )
            
            return QueryPlan(
                query_type=query_type,
                original_query=query,
                entities_mentioned=entities,
                time_range=time_range,
                requires_graph=query_type in [QueryType.MULTI_HOP, QueryType.CONTRADICTION],
                requires_temporal=query_type == QueryType.TEMPORAL,
                reasoning=reasoning
            )
            
        except json.JSONDecodeError as e:
            logger.warning("llm_json_parse_failed", error=str(e))
            return None
        except Exception as e:
            logger.warning("llm_classify_error", error=str(e))
            return None
    
    def get_retrieval_strategy(self, plan: QueryPlan) -> dict:
        """
        Get retrieval configuration based on query plan.
        
        Returns dict with:
        - dense_k: Number of dense results to fetch
        - sparse_k: Number of BM25 results to fetch  
        - graph_hops: Max graph traversal depth (0 = no graph)
        - temporal_sort: Whether to sort by time
        """
        strategies = {
            QueryType.SIMPLE: {
                "dense_k": 5,
                "sparse_k": 3,
                "graph_hops": 0,
                "temporal_sort": False,
                "reasoning": "Direct retrieval - semantic similarity"
            },
            QueryType.MULTI_HOP: {
                "dense_k": 3,
                "sparse_k": 2,
                "graph_hops": 3,
                "temporal_sort": False,
                "reasoning": "Graph traversal between entities + supporting docs"
            },
            QueryType.TEMPORAL: {
                "dense_k": 10,
                "sparse_k": 5,
                "graph_hops": 0,
                "temporal_sort": True,
                "reasoning": "Timeline query - fetch more, sort by time"
            },
            QueryType.CONTRADICTION: {
                "dense_k": 5,
                "sparse_k": 5,
                "graph_hops": 2,
                "temporal_sort": True,
                "reasoning": "Find conflicting statements - need multiple sources"
            },
            QueryType.AGGREGATION: {
                "dense_k": 15,
                "sparse_k": 10,
                "graph_hops": 0,
                "temporal_sort": False,
                "reasoning": "Broad retrieval for summarization"
            },
        }
        
        return strategies.get(plan.query_type, strategies[QueryType.SIMPLE])

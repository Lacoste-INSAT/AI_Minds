"""
Synapsis Reasoning Engine - Query Planner
Classifies incoming queries and routes to appropriate retrieval strategy.

Query Types:
- SIMPLE: Direct lookup ("What is X?") -> dense vector search
- MULTI_HOP: Relationship queries ("Ideas from Y about X") -> graph + vector
- TEMPORAL: Timeline queries ("How did my view change?") -> belief timeline
- CONTRADICTION: Belief conflicts ("Did I say conflicting things?") -> belief diff
"""
import json
import logging
import re
from typing import Optional

from .models import QueryPlan, QueryType
from .ollama_client import generate_completion, ModelTier


logger = logging.getLogger(__name__)

# System prompt for query classification
QUERY_PLANNER_SYSTEM_PROMPT = """You are a query classifier for a personal knowledge management system.
Your job is to classify user questions into exactly one of these categories:

1. SIMPLE - Direct factual lookup. Examples:
   - "What is the deadline for project X?"
   - "What did the meeting notes say about Y?"
   - "What is Z?"

2. MULTI_HOP - Requires connecting information across multiple sources. Examples:
   - "What ideas did John share about the marketing strategy?"
   - "How does project A relate to project B?"
   - "What connections exist between X and Y?"

3. TEMPORAL - About changes over time or belief evolution. Examples:
   - "How did my view on X change?"
   - "What did I think about X last month vs now?"
   - "When did I first mention Y?"

4. CONTRADICTION - Looking for conflicts in past statements. Examples:
   - "Did I say conflicting things about X?"
   - "Are there inconsistencies in my notes about Y?"
   - "What contradictions exist?"

Respond with a JSON object containing:
{
    "query_type": "SIMPLE" | "MULTI_HOP" | "TEMPORAL" | "CONTRADICTION",
    "entities": ["list", "of", "key", "entities", "in", "query"],
    "reasoning": "Brief explanation of why this classification"
}"""


# Heuristic patterns for fast classification (no LLM needed)
TEMPORAL_PATTERNS = [
    r"how\s+(did|has)\s+my\s+(view|opinion|thought|thinking|belief)",
    r"change[sd]?\s+over\s+time",
    r"(last|this)\s+(week|month|year)",
    r"when\s+did\s+i\s+(first|last)",
    r"evolution\s+of",
    r"timeline\s+of",
    r"history\s+of\s+my",
]

CONTRADICTION_PATTERNS = [
    r"contradict",
    r"conflict(ing|s)?",
    r"inconsisten",
    r"disagree",
    r"did\s+i\s+say\s+(different|conflicting)",
]

MULTI_HOP_PATTERNS = [
    r"(relate|connect|link)(s|ed|ion|ions)?\s+(to|between|with)",
    r"(relationship|connection)s?\s+(between|among)",
    r"how\s+does\s+.+\s+connect",
    r"what\s+(did\s+)?\w+\s+(say|said|share|shared|mention|mentioned)\s+about",
    r"from\s+.+\s+about",
    r"ideas?\s+from\s+\w+",
    r"connections?\s+exist",
]


def _classify_by_heuristics(query: str) -> Optional[QueryType]:
    """
    Fast classification using regex patterns.
    Returns None if no confident match - falls through to LLM.
    """
    query_lower = query.lower()
    
    # Check each pattern set
    for pattern in TEMPORAL_PATTERNS:
        if re.search(pattern, query_lower):
            return QueryType.TEMPORAL
    
    for pattern in CONTRADICTION_PATTERNS:
        if re.search(pattern, query_lower):
            return QueryType.CONTRADICTION
    
    for pattern in MULTI_HOP_PATTERNS:
        if re.search(pattern, query_lower):
            return QueryType.MULTI_HOP
    
    return None  # No confident match, use LLM


def _extract_entities_basic(query: str) -> list[str]:
    """
    Basic entity extraction without spaCy (fast fallback).
    Extracts quoted strings and capitalized words.
    """
    entities = []
    
    # Extract quoted strings
    quoted = re.findall(r'"([^"]+)"', query)
    entities.extend(quoted)
    quoted_single = re.findall(r"'([^']+)'", query)
    entities.extend(quoted_single)
    
    # Extract capitalized words (likely proper nouns)
    # Skip common words that might be capitalized
    skip_words = {"what", "who", "when", "where", "why", "how", "the", "a", "an", 
                  "is", "are", "was", "were", "did", "does", "do", "i", "my",
                  "to", "went", "from", "in", "on", "at", "for", "with"}
    
    # Find all capitalized words in the query (not just after first word)
    # Use regex to find capitalized words
    cap_words = re.findall(r'\b([A-Z][a-z]+)\b', query)
    
    # Common sentence starters that are capitalized just for grammar, not because they're proper nouns
    sentence_starters = {"please", "thanks", "hello", "hi", "hey", "well", "so", 
                         "now", "then", "here", "there", "yes", "no", "sure", 
                         "okay", "ok", "just", "also", "maybe", "perhaps",
                         "sorry", "great", "good", "nice", "fine", "could", 
                         "would", "should", "can", "will", "shall", "may", "let"}
    
    # Get the first word of the query to potentially skip it
    first_word_match = re.match(r'^([A-Z][a-z]+)\b', query)
    first_word = first_word_match.group(1) if first_word_match else None
    
    for word in cap_words:
        clean_word = re.sub(r'[^\w]', '', word)
        # Skip first word only if it's a common sentence starter (capitalized just for grammar)
        if clean_word == first_word and clean_word.lower() in sentence_starters:
            continue
        if clean_word and clean_word.lower() not in skip_words:
            entities.append(clean_word)
    
    return list(set(entities))


async def classify_query(query: str, use_llm: bool = True) -> QueryPlan:
    """
    Classify a user query and extract relevant entities.
    
    Strategy:
    1. Try fast heuristic classification first
    2. Fall back to LLM if heuristics uncertain
    3. Default to SIMPLE if LLM fails
    """
    # Step 1: Try heuristics (fast, no LLM call)
    heuristic_type = _classify_by_heuristics(query)
    
    if heuristic_type is not None:
        logger.info(f"Query classified by heuristics: {heuristic_type.value}")
        entities = _extract_entities_basic(query)
        return QueryPlan(
            query_type=heuristic_type,
            original_query=query,
            entities_detected=entities,
            reasoning=f"Classified by pattern matching as {heuristic_type.value}",
        )
    
    # Step 2: Use LLM for classification (if enabled)
    if use_llm:
        try:
            response = await generate_completion(
                prompt=f"Classify this query: {query}",
                system_prompt=QUERY_PLANNER_SYSTEM_PROMPT,
                json_mode=True,
                tier=ModelTier.T3,  # Use smallest model for classification
            )
            
            if response.success and response.content:
                try:
                    result = json.loads(response.content)
                    query_type_str = result.get("query_type", "SIMPLE").upper()
                    
                    # Validate query type
                    try:
                        query_type = QueryType(query_type_str)
                    except ValueError:
                        query_type = QueryType.SIMPLE
                    
                    entities = result.get("entities", [])
                    if not entities:
                        entities = _extract_entities_basic(query)
                    
                    logger.info(f"Query classified by LLM: {query_type.value}")
                    return QueryPlan(
                        query_type=query_type,
                        original_query=query,
                        entities_detected=entities,
                        reasoning=result.get("reasoning", ""),
                    )
                    
                except json.JSONDecodeError:
                    logger.warning("LLM returned invalid JSON, using fallback")
                    
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
    
    # Step 3: Default to SIMPLE
    logger.info("Defaulting to SIMPLE classification")
    return QueryPlan(
        query_type=QueryType.SIMPLE,
        original_query=query,
        entities_detected=_extract_entities_basic(query),
        reasoning="Default classification (heuristics uncertain, LLM unavailable)",
    )


async def plan_query(query: str) -> QueryPlan:
    """
    Main entry point for query planning.
    Returns a QueryPlan with classification and detected entities.
    """
    return await classify_query(query, use_llm=True)

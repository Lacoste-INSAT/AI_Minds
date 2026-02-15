"""
Synapsis Backend — Entity Extraction
3-layer extraction: Regex → spaCy NER → LLM concepts/relationships.
"""

from __future__ import annotations

import re
import json
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ExtractedEntity:
    name: str
    entity_type: str
    source: str  # "regex" | "spacy" | "llm"


@dataclass
class ExtractedRelationship:
    source_entity: str
    target_entity: str
    relation_type: str


@dataclass
class ExtractionResult:
    entities: list[ExtractedEntity] = field(default_factory=list)
    relationships: list[ExtractedRelationship] = field(default_factory=list)


def extract_regex(text: str) -> list[ExtractedEntity]:
    """Layer 1: Regex patterns (EMAIL, URL, DATE, MONEY, PHONE, TECHNOLOGY)."""
    entities = []
    
    # Email pattern
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    for email in emails:
        entities.append(ExtractedEntity(name=email, entity_type="email", source="regex"))
    
    # URL pattern
    urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
    for url in urls[:5]:  # Limit to 5 URLs
        entities.append(ExtractedEntity(name=url[:100], entity_type="url", source="regex"))
    
    # Technology terms (common ML/AI/Software terms)
    tech_patterns = [
        r'\b(Python|JavaScript|TypeScript|Rust|Go|Java|C\+\+|Ruby|PHP|Swift|Kotlin)\b',
        r'\b(React|Vue|Angular|Next\.js|FastAPI|Django|Flask|Express|Node\.js)\b',
        r'\b(PostgreSQL|MySQL|SQLite|MongoDB|Redis|Qdrant|Elasticsearch)\b',
        r'\b(Docker|Kubernetes|AWS|Azure|GCP|Ollama|OpenAI|Anthropic|LangChain)\b',
        r'\b(RAG|LLM|NLP|ML|AI|GPU|CPU|API|REST|GraphQL|SSE|WebSocket)\b',
        r'\b(BERT|GPT|Transformer|Embedding|Vector|Neural|Model)\b',
        r'\b(qwen|phi4|llama|mistral|gemma)\d*\.?\d*b?\b',
    ]
    
    found_tech = set()
    for pattern in tech_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if match.lower() not in found_tech:
                found_tech.add(match.lower())
                entities.append(ExtractedEntity(
                    name=match, 
                    entity_type="technology", 
                    source="regex"
                ))
    
    # Date patterns (simple)
    dates = re.findall(r'\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b', text, re.IGNORECASE)
    for date in dates[:3]:
        entities.append(ExtractedEntity(name=date, entity_type="date", source="regex"))
    
    return entities


def extract_spacy(text: str) -> list[ExtractedEntity]:
    """Layer 2: spaCy en_core_web_sm NER (PERSON, ORG, GPE, etc.)."""
    # Skip spaCy for now - requires model download
    return []


async def extract_llm(text: str) -> ExtractionResult:
    """Layer 3: LLM-based concept + relationship extraction."""
    from backend.services.ollama_client import ollama_client
    
    # Limit text length for LLM
    truncated = text[:1500] if len(text) > 1500 else text
    
    prompt = f"""Extract key concepts and relationships from this text. Return ONLY valid JSON.

Text: {truncated}

Return JSON in this exact format:
{{"entities": [{{"name": "string", "type": "concept|person|project|tool"}}], "relationships": [{{"source": "entity1", "target": "entity2", "relation": "uses|mentions|related_to"}}]}}"""

    try:
        response = await ollama_client.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=500,
        )
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            entities = [
                ExtractedEntity(
                    name=e.get("name", ""),
                    entity_type=e.get("type", "concept"),
                    source="llm"
                )
                for e in data.get("entities", [])
                if e.get("name")
            ]
            relationships = [
                ExtractedRelationship(
                    source_entity=r.get("source", ""),
                    target_entity=r.get("target", ""),
                    relation_type=r.get("relation", "related_to")
                )
                for r in data.get("relationships", [])
                if r.get("source") and r.get("target")
            ]
            return ExtractionResult(entities=entities, relationships=relationships)
    except json.JSONDecodeError as e:
        logger.warning("entity_extraction.llm_json_error", error=str(e))
    except Exception as e:
        logger.warning("entity_extraction.llm_error", error=str(e))
    
    return ExtractionResult()


async def extract_entities(text: str) -> ExtractionResult:
    """Run all 3 layers and return merged, deduplicated results."""
    # Layer 1: Regex
    regex_entities = extract_regex(text)
    
    # Layer 2: spaCy (skipped for now)
    spacy_entities = extract_spacy(text)
    
    # Layer 3: LLM (only for longer texts)
    llm_result = ExtractionResult()
    if len(text) > 200:
        try:
            llm_result = await extract_llm(text)
        except Exception as e:
            logger.warning("entity_extraction.llm_failed", error=str(e))
    
    # Merge and deduplicate
    all_entities = regex_entities + spacy_entities + llm_result.entities
    seen = set()
    unique_entities = []
    for entity in all_entities:
        key = (entity.name.lower(), entity.entity_type)
        if key not in seen:
            seen.add(key)
            unique_entities.append(entity)
    
    return ExtractionResult(
        entities=unique_entities,
        relationships=llm_result.relationships
    )

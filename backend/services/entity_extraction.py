"""
Synapsis Backend — Entity Extraction
3-layer extraction: Regex → spaCy NER → co-occurrence relationships.

Layer 1  – Regex patterns (EMAIL, URL, DATE, MONEY, PHONE)
Layer 2  – spaCy ``en_core_web_sm`` NER (PERSON, ORG, GPE, …)
Layer 3  – Co-occurrence relationship extraction
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from itertools import combinations

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Layer 1 — Regex-based extraction
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
_URL_RE = re.compile(r"https?://[^\s<>\"']+")
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"
)
_MONEY_RE = re.compile(
    r"\$\s?\d[\d,]*(?:\.\d{1,2})?(?:\s?(?:million|billion|M|B|K|k))?"
    r"|(?:\d[\d,]*(?:\.\d{1,2})?\s?(?:USD|EUR|GBP|TND|dollars?))",
    re.IGNORECASE,
)
_DATE_RE = re.compile(
    r"\b(?:"
    r"\d{4}[-/]\d{1,2}[-/]\d{1,2}"                              # 2026-02-15
    r"|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}"                           # 02/15/2026
    r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"[a-z]*\.?\s+\d{1,2},?\s+\d{4}"                            # February 14, 2026
    r"|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"[a-z]*\.?\s+\d{4}"                                        # 14 Feb 2026
    r")\b",
    re.IGNORECASE,
)


def extract_regex(text: str) -> list[ExtractedEntity]:
    """Layer 1: Regex patterns (EMAIL, URL, DATE, MONEY, PHONE)."""
    entities: list[ExtractedEntity] = []

    for match in _EMAIL_RE.finditer(text):
        entities.append(ExtractedEntity(name=match.group(), entity_type="EMAIL", source="regex"))

    for match in _URL_RE.finditer(text):
        entities.append(ExtractedEntity(name=match.group(), entity_type="URL", source="regex"))

    for match in _PHONE_RE.finditer(text):
        val = match.group().strip()
        if len(re.sub(r"\D", "", val)) >= 7:  # at least 7 digits
            entities.append(ExtractedEntity(name=val, entity_type="PHONE", source="regex"))

    for match in _MONEY_RE.finditer(text):
        entities.append(ExtractedEntity(name=match.group().strip(), entity_type="MONEY", source="regex"))

    for match in _DATE_RE.finditer(text):
        entities.append(ExtractedEntity(name=match.group().strip(), entity_type="DATE", source="regex"))

    return entities


# ---------------------------------------------------------------------------
# Layer 2 — spaCy NER
# ---------------------------------------------------------------------------

_nlp = None

# Map spaCy labels to our entity types
_SPACY_LABEL_MAP = {
    "PERSON": "PERSON",
    "ORG": "ORGANIZATION",
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "FAC": "LOCATION",
    "PRODUCT": "PRODUCT",
    "EVENT": "EVENT",
    "WORK_OF_ART": "WORK_OF_ART",
    "LAW": "LAW",
    "LANGUAGE": "LANGUAGE",
    "NORP": "GROUP",         # Nationalities, religious/political groups
    "DATE": "DATE",
    "TIME": "TIME",
    "MONEY": "MONEY",
    "QUANTITY": "QUANTITY",
    "PERCENT": "PERCENT",
    "ORDINAL": "ORDINAL",
    "CARDINAL": "CARDINAL",
}

# Entity types we *always* want to keep (high-value for knowledge graph)
_HIGH_VALUE_TYPES = {"PERSON", "ORGANIZATION", "LOCATION", "PRODUCT", "EVENT", "GROUP"}

# Low-value spaCy labels we skip entirely
_SKIP_TYPES = {"CARDINAL", "ORDINAL", "QUANTITY", "PERCENT"}

# Common spaCy false-positives on technical / conversational text.
# Lowercase, checked against ``name.lower()``.
_ENTITY_BLOCKLIST: set[str] = {
    # Generic nouns wrongly tagged as PERSON
    "key decisions", "key decision", "next steps", "action items",
    "the team", "the user", "someone", "everyone", "anyone",
    # Tech terms wrongly tagged as ORG / PRODUCT
    "websocket", "websockets", "json", "http", "https", "api",
    "rest", "graphql", "sql", "sqlite", "docker", "linux",
    "github", "ollama", "ollama for llm", "llm", "rag",
    "fastapi", "pydantic", "uvicorn", "python", "javascript",
    "typescript", "react", "nextjs", "next.js", "node", "npm",
    "frontend", "backend", "readme", "markdown", "yaml", "csv",
    # Misc noise
    "today", "yesterday", "tomorrow", "monday", "tuesday",
    "wednesday", "thursday", "friday", "saturday", "sunday",
}


def _get_nlp():
    """Lazy-load spaCy model."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
            logger.info("entity_extraction.spacy_loaded", model="en_core_web_sm")
        except Exception as exc:
            logger.warning("entity_extraction.spacy_unavailable", error=str(exc))
            _nlp = False  # Sentinel: tried and failed
    return _nlp if _nlp is not False else None


def extract_spacy(text: str) -> list[ExtractedEntity]:
    """Layer 2: spaCy en_core_web_sm NER (PERSON, ORG, GPE, etc.)."""
    nlp = _get_nlp()
    if nlp is None:
        return []

    # Truncate very long texts to avoid slow processing
    max_chars = 100_000
    doc = nlp(text[:max_chars])

    seen: set[tuple[str, str]] = set()
    entities: list[ExtractedEntity] = []

    for ent in doc.ents:
        name = ent.text.strip()

        # --- Quality filters ---
        # Skip very short / very long / multiline names
        if len(name) < 2 or len(name) > 80 or "\n" in name:
            continue

        # Must contain at least one letter (skip pure numbers / punctuation)
        if not any(c.isalpha() for c in name):
            continue

        entity_type = _SPACY_LABEL_MAP.get(ent.label_, ent.label_)

        # Skip low-value numeric types (CARDINAL, ORDINAL, QUANTITY, PERCENT)
        if entity_type in {"CARDINAL", "ORDINAL", "QUANTITY", "PERCENT"}:
            continue

        # Skip if the text looks like an email/URL already handled by regex
        if "@" in name or name.startswith("http"):
            continue

        # Skip blocklisted names (common false positives)
        if name.lower() in _ENTITY_BLOCKLIST:
            continue

        key = (name.lower(), entity_type)
        if key in seen:
            continue
        seen.add(key)

        entities.append(ExtractedEntity(name=name, entity_type=entity_type, source="spacy"))

    return entities


# ---------------------------------------------------------------------------
# Layer 3 — Co-occurrence relationship extraction
# ---------------------------------------------------------------------------

# Maximum co-occurrence edges per chunk.  Keeps the graph from drowning in
# O(n²) noise.  With 20 entities that's 190 pairs — we only keep the top 15.
_MAX_COOCCURRENCE_PER_CHUNK = 15


def _extract_cooccurrence_relationships(
    entities: list[ExtractedEntity],
) -> list[ExtractedRelationship]:
    """
    Build relationships from entity co-occurrence.

    If two high-value entities appear in the same text chunk, they are
    likely related.  We create a "co-occurs_with" edge by default, and
    refine to more specific types when possible (e.g. PERSON↔ORG →
    "affiliated_with").

    Capped at ``_MAX_COOCCURRENCE_PER_CHUNK`` to prevent edge explosion.
    Prioritises specific relationship types over generic "co_occurs_with".
    """
    high_value = [e for e in entities if e.entity_type in _HIGH_VALUE_TYPES]

    if len(high_value) < 2:
        return []

    relationships: list[ExtractedRelationship] = []
    seen_pairs: set[tuple[str, str]] = set()

    for a, b in combinations(high_value, 2):
        pair = tuple(sorted([a.name.lower(), b.name.lower()]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        rel_type = _infer_relation(a.entity_type, b.entity_type)
        relationships.append(
            ExtractedRelationship(
                source_entity=a.name,
                target_entity=b.name,
                relation_type=rel_type,
            )
        )

    # Prioritise specific types, then cap
    _specificity = {
        "co_occurs_with": 0,
        "related_to": 1,
        "associated_with": 2,
    }
    relationships.sort(
        key=lambda r: _specificity.get(r.relation_type, 10), reverse=True
    )
    return relationships[:_MAX_COOCCURRENCE_PER_CHUNK]


def _infer_relation(type_a: str, type_b: str) -> str:
    """Heuristic relationship label from entity-type pair."""
    pair = frozenset([type_a, type_b])

    if pair == {"PERSON", "ORGANIZATION"}:
        return "affiliated_with"
    if pair == {"PERSON", "LOCATION"}:
        return "located_in"
    if pair == {"ORGANIZATION", "LOCATION"}:
        return "based_in"
    if pair == {"PERSON", "EVENT"}:
        return "participated_in"
    if pair == {"ORGANIZATION", "EVENT"}:
        return "involved_in"
    if pair == {"PERSON", "PRODUCT"}:
        return "works_on"
    if pair == {"ORGANIZATION", "PRODUCT"}:
        return "produces"
    if type_a == type_b == "PERSON":
        return "associated_with"
    if type_a == type_b == "ORGANIZATION":
        return "related_to"

    return "co_occurs_with"


# ---------------------------------------------------------------------------
# Public API — combined extraction
# ---------------------------------------------------------------------------


def _deduplicate_entities(entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
    """Deduplicate entities by (lowercase name, type), keeping first source."""
    seen: dict[tuple[str, str], ExtractedEntity] = {}
    for ent in entities:
        key = (ent.name.lower().strip(), ent.entity_type)
        if key not in seen:
            seen[key] = ent
    return list(seen.values())


async def extract_llm(text: str) -> ExtractionResult:
    """Layer 3: LLM-based concept + relationship extraction.

    Currently a no-op placeholder.  When an Ollama model is available
    this can be swapped in for deeper semantic extraction.
    """
    return ExtractionResult()


async def extract_entities(text: str) -> ExtractionResult:
    """
    Run all extraction layers and return merged, deduplicated results.

    1. Regex → emails, URLs, dates, money, phones
    2. spaCy → PERSON, ORG, GPE, PRODUCT, EVENT, …
    3. Co-occurrence → relationships between high-value entities
    """
    if not text or not text.strip():
        return ExtractionResult()

    # Layer 1 — regex
    regex_ents = extract_regex(text)

    # Layer 2 — spaCy NER
    spacy_ents = extract_spacy(text)

    # Merge & deduplicate
    all_entities = _deduplicate_entities(regex_ents + spacy_ents)

    # Layer 3 — co-occurrence relationships
    relationships = _extract_cooccurrence_relationships(all_entities)

    logger.debug(
        "entity_extraction.complete",
        regex=len(regex_ents),
        spacy=len(spacy_ents),
        merged=len(all_entities),
        relationships=len(relationships),
    )

    return ExtractionResult(entities=all_entities, relationships=relationships)

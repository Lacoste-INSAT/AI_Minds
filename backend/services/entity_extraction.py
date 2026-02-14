"""
Synapsis Backend — Entity Extraction (Person 3)
3-layer extraction: Regex → spaCy NER → LLM concepts/relationships.

TODO (Person 3): Implement all 3 extraction layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field


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
    """Layer 1: Regex patterns (EMAIL, URL, DATE, MONEY, PHONE)."""
    return []  # TODO Person 3


def extract_spacy(text: str) -> list[ExtractedEntity]:
    """Layer 2: spaCy en_core_web_sm NER (PERSON, ORG, GPE, etc.)."""
    return []  # TODO Person 3


async def extract_llm(text: str) -> ExtractionResult:
    """Layer 3: LLM-based concept + relationship extraction."""
    return ExtractionResult()  # TODO Person 3


async def extract_entities(text: str) -> ExtractionResult:
    """Run all 3 layers and return merged, deduplicated results."""
    return ExtractionResult()  # TODO Person 3

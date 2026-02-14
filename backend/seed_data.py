"""
Seed Demo Data for Synapsis

Loads real demonstration data into the knowledge base.
All data uses real, verifiable information (model specs, benchmarks, papers).

Run with: python -m backend.seed_data
"""

import asyncio
from pathlib import Path
from datetime import datetime
import hashlib
from typing import List, Tuple
import re

from backend.database import memory_db

# Sample data directory
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "data" / "sample_knowledge"


def extract_entities_simple(content: str) -> List[Tuple[str, str]]:
    """
    Entity extraction from markdown content using pattern matching.
    Extracts real models, tools, papers, and technologies referenced in the data.
    Returns list of (name, type) tuples.
    """
    entities = []

    # Extract LLM models (real models from our evaluation)
    model_patterns = [
        r'\b(Phi-4-mini(?:-instruct)?)\b',
        r'\b(Qwen2\.5-3B(?:-Instruct)?)\b',
        r'\b(Qwen2\.5-0\.5B)\b',
        r'\b(Llama-3\.2-3B(?:-Ins(?:truct)?)?)\b',
        r'\b(Mistral-3B)\b',
        r'\b(nomic-embed-text(?:-v1\.5)?)\b',
        r'\b(all-MiniLM-L6-v2)\b',
        r'\b(mxbai-embed-large(?:-v1)?)\b',
        r'\b(bge-base-en-v1\.5)\b',
    ]
    for pattern in model_patterns:
        if re.search(pattern, content):
            name = re.search(pattern, content).group(1)
            entities.append((name, "model"))

    # Extract organizations
    org_patterns = [
        r'\b(Microsoft)\b',
        r'\b(Alibaba)\b',
        r'\b(Meta)\b',
        r'\b(Mistral AI)\b',
    ]
    for pattern in org_patterns:
        if re.search(pattern, content):
            name = re.search(pattern, content).group(1)
            entities.append((name, "organization"))

    # Extract projects/systems
    project_patterns = [
        r'\b(Synapsis)\b',
    ]
    for pattern in project_patterns:
        if re.search(pattern, content):
            name = re.search(pattern, content).group(1)
            entities.append((name, "project"))

    # Extract technologies / tools
    tech_patterns = [
        r'\b(Qdrant|Ollama|FastAPI|SQLite|NetworkX|Next\.js)\b',
        r'\b(FTS5|HNSW|RRF|BM25|DPR|GQA)\b',
        r'\b(Transformers|RoPE|SwiGLU|RMSNorm)\b',
    ]
    for pattern in tech_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            entities.append((match, "technology"))

    # Extract benchmarks
    benchmark_patterns = [
        r'\b(MMLU(?:-Pro)?)\b',
        r'\b(GSM8K)\b',
        r'\b(MATH)\b',
        r'\b(HellaSwag)\b',
        r'\b(ARC Challenge)\b',
        r'\b(TruthfulQA)\b',
        r'\b(BigBench Hard)\b',
        r'\b(MTEB)\b',
    ]
    for pattern in benchmark_patterns:
        if re.search(pattern, content):
            name = re.search(pattern, content).group(1)
            entities.append((name, "benchmark"))

    # Extract research papers / authors
    paper_patterns = [
        r'\b(Lewis et al\.?)\b',
        r'\b(Gao et al\.?)\b',
        r'\b(Karpukhin et al\.?)\b',
        r'\b(Cormack et al\.?)\b',
    ]
    for pattern in paper_patterns:
        if re.search(pattern, content):
            name = re.search(pattern, content).group(1)
            entities.append((name, "paper_author"))

    # Extract dates
    date_patterns = [
        r'\b(February \d{1,2}, 2026)\b',
        r'\b(Feb(?:ruary)? \d{1,2}, 2026)\b',
        r'\b(January \d{1,2}, 2026)\b',
        r'\b(2026-\d{2}-\d{2})\b',
    ]
    for pattern in date_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            entities.append((match, "date"))

    # Deduplicate while preserving order
    seen = set()
    unique_entities = []
    for entity in entities:
        if entity not in seen:
            seen.add(entity)
            unique_entities.append(entity)

    return unique_entities


def extract_tags(content: str, file_path: str) -> List[str]:
    """Extract tags from content and file path."""
    tags = []

    # From directory structure
    path_parts = Path(file_path).parts
    if "notes" in path_parts:
        tags.append("notes")
    if "research" in path_parts:
        tags.append("research")
    if "journal" in path_parts:
        tags.append("journal")

    # From content keywords — all real topics, no fictional scenarios
    content_lower = content.lower()
    if "decision" in content_lower:
        tags.append("decision")
    if "architecture" in content_lower:
        tags.append("architecture")
    if "benchmark" in content_lower:
        tags.append("benchmark")
    if "embedding" in content_lower:
        tags.append("embedding")
    if "retrieval" in content_lower:
        tags.append("retrieval")
    if "model" in content_lower and "evaluation" in content_lower:
        tags.append("evaluation")
    if "rag" in content_lower:
        tags.append("rag")

    # Extract inline tags from metadata header if present
    tag_match = re.search(r'\*\*Tags:\*\*\s*(.+)', content)
    if tag_match:
        inline_tags = [t.strip() for t in tag_match.group(1).split(",")]
        tags.extend(inline_tags)

    return list(set(tags))


def determine_source_type(file_path: str, content: str) -> str:
    """Determine the type of document."""
    path_parts = Path(file_path).parts
    
    if "people" in path_parts:
        return "person_profile"
    if "journal" in path_parts:
        return "journal"
    if "research" in path_parts:
        return "research"
    if "meeting" in file_path.lower() or "## attendees" in content.lower():
        return "meeting"
    if "spec" in file_path.lower():
        return "specification"
    return "note"


def parse_document_dates(content: str, file_path: str) -> Tuple[datetime, datetime]:
    """Parse created and modified dates from content."""
    # Try to find dates in document metadata
    created_match = re.search(r'\*\*Created\*\*:\s*(\d{4}-\d{2}-\d{2})', content)
    modified_match = re.search(r'\*\*Last Modified\*\*:\s*(\d{4}-\d{2}-\d{2})', content)
    
    if created_match:
        created = datetime.strptime(created_match.group(1), "%Y-%m-%d")
    else:
        created = datetime(2026, 1, 15)  # Default
    
    if modified_match:
        modified = datetime.strptime(modified_match.group(1), "%Y-%m-%d")
    else:
        modified = datetime(2026, 2, 10)  # Default
    
    return created, modified


async def seed_sample_data():
    """
    Load sample markdown files into the database.
    """
    await memory_db.initialize()
    
    print("[SEED] Seeding demo data from sample_knowledge/...")
    
    # Find all markdown files
    md_files = list(SAMPLE_DATA_DIR.rglob("*.md"))
    
    if not md_files:
        print(f"[WARN] No markdown files found in {SAMPLE_DATA_DIR}")
        return
    
    print(f"[INFO] Found {len(md_files)} markdown files")
    
    entity_cache = {}  # Track inserted entities
    relationships = []  # Collect relationships to add
    
    for md_file in md_files:
        print(f"  Processing: {md_file.name}")
        
        content = md_file.read_text(encoding="utf-8")
        title = md_file.stem.replace("_", " ").title()
        
        # Get dates
        created, modified = parse_document_dates(content, str(md_file))
        
        # Extract entities and tags
        entities = extract_entities_simple(content)
        tags = extract_tags(content, str(md_file))
        source_type = determine_source_type(str(md_file), content)
        
        # Insert memory
        memory_id = await memory_db.insert_memory(
            title=title,
            content=content,
            source_type=source_type,
            file_path=str(md_file.relative_to(SAMPLE_DATA_DIR)),
            created_at=created,
            modified_at=modified,
            tags=tags
        )
        
        # Insert entities and track mentions
        for entity_name, entity_type in entities:
            if entity_name not in entity_cache:
                entity_id = await memory_db.insert_entity(
                    name=entity_name,
                    entity_type=entity_type
                )
                entity_cache[entity_name] = entity_id
            else:
                entity_id = entity_cache[entity_name]
            
            # Add mention
            await memory_db.add_entity_mention(
                entity_id=entity_id,
                memory_id=memory_id
            )
        
        # Collect relationships based on co-occurrence in documents
        models = [e[0] for e in entities if e[1] == "model"]
        techs = [e[0] for e in entities if e[1] == "technology"]
        benchmarks = [e[0] for e in entities if e[1] == "benchmark"]
        projects = [e[0] for e in entities if e[1] == "project"]

        # Models evaluated on benchmarks
        for model in models:
            for benchmark in benchmarks:
                relationships.append((model, benchmark, "evaluated_on", memory_id))

        # Models use technologies
        for model in models:
            for tech in techs:
                relationships.append((model, tech, "related_to", memory_id))

        # Project uses models
        for project in projects:
            for model in models:
                relationships.append((project, model, "uses", memory_id))

        # Project uses technologies
        for project in projects:
            for tech in techs:
                relationships.append((project, tech, "uses", memory_id))

        # Models compared with each other
        for i, m1 in enumerate(models):
            for m2 in models[i+1:]:
                relationships.append((m1, m2, "compared_with", memory_id))
    
    # Add relationships (deduplicated)
    seen_relationships = set()
    for source, target, rel_type, evidence in relationships:
        key = (source, target, rel_type)
        if key not in seen_relationships:
            seen_relationships.add(key)
            source_id = entity_cache.get(source)
            target_id = entity_cache.get(target)
            if source_id and target_id:
                await memory_db.add_relationship(
                    source_entity=source_id,
                    target_entity=target_id,
                    relationship_type=rel_type,
                    evidence_memory_id=evidence
                )
    
    # Add insights based on real data patterns
    await memory_db.add_insight(
        insight_type="contradiction",
        title="Model selection changed",
        description="On Feb 5 Qwen2.5-3B was selected as primary model, but on Feb 7 the decision was reversed to Phi-4-mini based on GSM8K benchmark results (88.6 vs 80.6). The model_selection_log.md documents this evolution.",
        related_documents=["model_selection_log.md", "phi4_mini_model_card.md"]
    )

    await memory_db.add_insight(
        insight_type="contradiction",
        title="Embedding model decision changed",
        description="Initial plan (Feb 6) was to use all-MiniLM-L6-v2 for speed, but was replaced by nomic-embed-text on Feb 11 due to unacceptable retrieval score (41.9 vs 53.1). See embedding_model_comparison.md.",
        related_documents=["embedding_model_comparison.md", "model_selection_log.md"]
    )

    await memory_db.add_insight(
        insight_type="pattern",
        title="Hybrid retrieval outperforms single methods",
        description="Testing shows hybrid RRF retrieval achieves 0.86 average recall vs 0.64 (dense only) and 0.65 (sparse only) — a consistent 21+ point improvement across all query types.",
        related_documents=["hybrid_retrieval.md", "february_2026_devlog.md"]
    )
    
    # Get stats
    stats = await memory_db.get_stats()
    
    print("\n[DONE] Seeding complete!")
    print(f"   Documents: {stats['total_documents']}")
    print(f"   Entities: {stats['total_entities']}")
    print(f"   Relationships: {stats['total_relationships']}")
    print(f"   Storage: {stats['storage_used_mb']:.2f} MB")


if __name__ == "__main__":
    asyncio.run(seed_sample_data())

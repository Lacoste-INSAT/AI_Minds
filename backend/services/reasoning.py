"""
Synapsis Backend — Reasoning Engine
Query planner + LLM reasoning + critic verification + confidence scoring.
"""

from __future__ import annotations

import json
import re

import structlog

from backend.models.schemas import AnswerPacket, ChunkEvidence
from backend.services.ollama_client import ollama_client
from backend.services.retrieval import (
    RetrievalResult,
    hybrid_search,
    results_to_evidence,
)
from backend.services.embeddings import embed_text

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Query Planning
# ---------------------------------------------------------------------------

QUERY_PLANNER_PROMPT = """Classify this user question into one of these categories:
- SIMPLE: A straightforward factual question (e.g., "What is X?")
- MULTI_HOP: Requires connecting multiple pieces of information (e.g., "What did Y say about X?")
- TEMPORAL: About how something changed over time (e.g., "How did my view on X evolve?")
- CONTRADICTION: About conflicting information (e.g., "Did I say conflicting things about X?")
- AGGREGATION: Requires summarizing across multiple sources (e.g., "What are my top priorities?")

Respond with ONLY the category name, nothing else.

Question: {question}"""


async def classify_query(question: str) -> str:
    """Classify the query type using the LLM."""
    try:
        prompt = QUERY_PLANNER_PROMPT.format(question=question)
        response = await ollama_client.generate(
            prompt=prompt,
            system="You are a query classifier. Respond with ONLY the category name.",
            temperature=0.0,
            max_tokens=20,
        )
        classification = response.strip().upper()
        valid = {"SIMPLE", "MULTI_HOP", "TEMPORAL", "CONTRADICTION", "AGGREGATION"}
        if classification in valid:
            return classification
    except Exception as e:
        logger.warning("query_planner.classification_failed", error=str(e))

    return "SIMPLE"  # Default fallback


# ---------------------------------------------------------------------------
# Context Assembly
# ---------------------------------------------------------------------------


def assemble_context(results: list[RetrievalResult]) -> str:
    """Build a context string from retrieval results with source labels."""
    if not results:
        return "No relevant information found in your records."

    context_parts = []
    for i, r in enumerate(results, 1):
        context_parts.append(
            f"[Source {i}] (File: {r.file_name})\n{r.content}"
        )

    return "\n\n---\n\n".join(context_parts)


# ---------------------------------------------------------------------------
# Reasoning (LLM)
# ---------------------------------------------------------------------------

REASONING_PROMPT = """You are a personal knowledge assistant. Answer the user's question based ONLY on the provided sources.

Rules:
1. ONLY use information from the provided sources — never fabricate or assume.
2. Cite sources using [Source N] notation inline.
3. If the sources don't contain enough information, say so explicitly.
4. Be concise but thorough.
5. If sources conflict, mention the contradiction.

Sources:
{context}

Question: {question}

Answer:"""


async def reason(
    question: str,
    context: str,
    query_type: str = "SIMPLE",
) -> str:
    """Generate an answer using the LLM with retrieved context."""
    prompt = REASONING_PROMPT.format(context=context, question=question)

    system = (
        "You are Synapsis, a personal knowledge assistant. "
        "Answer questions grounded in the user's own data. "
        "Always cite sources. Never fabricate information."
    )

    response = await ollama_client.generate(
        prompt=prompt,
        system=system,
        temperature=0.3,
        max_tokens=2048,
    )

    return response.strip()


# ---------------------------------------------------------------------------
# Critic Agent — Self-Verification
# ---------------------------------------------------------------------------

CRITIC_PROMPT = """You are a verification agent. Review whether the given answer is properly supported by the sources.

Sources:
{context}

Question: {question}

Answer: {answer}

Evaluate:
1. Is every claim in the answer supported by at least one source?
2. Are the source citations accurate?
3. Did the answer fabricate any information not in the sources?

Respond with EXACTLY one of:
- APPROVE — if the answer is well-supported by sources
- REVISE — if partially supported but needs minor corrections
- REJECT — if the answer fabricates information or is not supported

Then on a new line, briefly explain why.

Verdict:"""


async def verify_answer(
    question: str,
    answer: str,
    context: str,
) -> tuple[str, str]:
    """
    Critic agent: verify the answer against sources.
    Returns (verdict, reasoning).
    """
    try:
        prompt = CRITIC_PROMPT.format(
            context=context, question=question, answer=answer
        )

        response = await ollama_client.generate(
            prompt=prompt,
            system="You are a strict verification agent. Be critical and fact-check carefully.",
            temperature=0.0,
            max_tokens=512,
        )

        lines = response.strip().split("\n", 1)
        verdict_line = lines[0].strip().upper()

        # Extract verdict
        verdict = "APPROVE"
        for v in ["APPROVE", "REVISE", "REJECT"]:
            if v in verdict_line:
                verdict = v
                break

        reasoning = lines[1].strip() if len(lines) > 1 else ""
        return verdict, reasoning

    except Exception as e:
        logger.warning("critic.verification_failed", error=str(e))
        return "REVISE", "Verification skipped due to error; answer requires manual review."


# ---------------------------------------------------------------------------
# Confidence Scoring
# ---------------------------------------------------------------------------


def compute_confidence(
    results: list[RetrievalResult],
    verdict: str,
) -> tuple[str, float, str | None]:
    """
    Compute confidence based on retrieval quality and critic verdict.
    Returns (level, score, uncertainty_reason).
    """
    if not results:
        return "none", 0.0, "No relevant sources found in your records."

    if verdict == "REJECT":
        return "low", 0.15, "Answer could not be verified against sources."

    # Top source score
    top_score = max(r.score_final for r in results) if results else 0.0

    # Source count factor
    source_count = len(results)
    source_count_factor = min(source_count / 3, 1.0)

    # Source agreement (simplified — based on score variance)
    scores = [r.score_final for r in results]
    if len(scores) > 1:
        avg = sum(scores) / len(scores)
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)
        agreement = max(0.0, 1.0 - variance * 10)
    else:
        agreement = 0.5

    # Recency factor (simplified — assume recent)
    recency = 0.8

    # Weighted score
    score = (
        0.3 * min(top_score, 1.0)
        + 0.3 * agreement
        + 0.2 * source_count_factor
        + 0.2 * recency
    )

    # Apply verdict penalty
    if verdict == "REVISE":
        score *= 0.8

    # Map to level
    if score >= 0.7:
        level = "high"
        reason = None
    elif score >= 0.4:
        level = "medium"
        reason = "Moderate confidence — sources partially cover the question."
    elif score >= 0.2:
        level = "low"
        reason = "Low confidence — limited source support."
    else:
        level = "none"
        reason = "Insufficient evidence to answer confidently."

    return level, round(score, 3), reason


# ---------------------------------------------------------------------------
# Full Query Pipeline (main entry point)
# ---------------------------------------------------------------------------


async def process_query(
    question: str,
    top_k: int = 10,
    include_graph: bool = True,
) -> AnswerPacket:
    """
    Full reasoning pipeline:
    1. Classify query
    2. Embed query
    3. Hybrid retrieval
    4. Assemble context
    5. LLM reasoning
    6. Critic verification
    7. Confidence scoring
    8. Return AnswerPacket
    """
    logger.info("query.processing", question=question[:100])

    # Step 1: Classify query
    query_type = await classify_query(question)
    logger.info("query.classified", type=query_type)

    # Step 2: Embed query (CPU-heavy — offload to threadpool)
    import asyncio
    query_vector = await asyncio.to_thread(embed_text, question)

    # Step 3: Hybrid retrieval
    results = await hybrid_search(
        query=question,
        query_vector=query_vector,
        top_k=top_k,
        include_graph=include_graph,
    )

    # Step 4: Assemble context
    context = assemble_context(results)

    # Step 5: Check if we have enough context
    if not results:
        return AnswerPacket(
            answer="I don't have enough information in your records to answer this question.",
            confidence="none",
            confidence_score=0.0,
            uncertainty_reason="No relevant sources found.",
            sources=[],
            verification="REJECT",
            reasoning_chain=f"Query type: {query_type}. No matching documents found.",
        )

    # Step 6: LLM reasoning
    answer = await reason(question, context, query_type)

    # Step 7: Critic verification
    verdict, critic_reasoning = await verify_answer(question, answer, context)

    # Handle REVISE — one retry
    if verdict == "REVISE":
        logger.info("query.revision_attempt")
        revision_prompt = (
            f"The previous answer needs revision. Feedback: {critic_reasoning}\n\n"
            f"Please provide a corrected answer based on the sources."
        )
        answer = await reason(
            question + "\n\n" + revision_prompt,
            context,
            query_type,
        )
        verdict, critic_reasoning = await verify_answer(question, answer, context)

    # Step 8: Confidence scoring
    confidence_level, confidence_score, uncertainty_reason = compute_confidence(
        results, verdict
    )

    # Handle abstention on REJECT
    if verdict == "REJECT":
        answer = (
            "I don't have enough information in your records to answer this confidently. "
            "Here's what I found that might be related:\n\n"
            + "\n".join(
                f"- [{r.file_name}]: {r.content[:200]}..."
                for r in results[:3]
            )
        )
        confidence_level = "none"
        confidence_score = 0.1

    # Build evidence
    sources = results_to_evidence(results)

    reasoning_chain = (
        f"Query type: {query_type}\n"
        f"Retrieval: {len(results)} chunks found\n"
        f"Verification: {verdict}\n"
        f"Critic: {critic_reasoning}"
    )

    logger.info(
        "query.complete",
        confidence=confidence_level,
        confidence_score=confidence_score,
        verdict=verdict,
        sources_count=len(sources),
    )

    return AnswerPacket(
        answer=answer,
        confidence=confidence_level,
        confidence_score=confidence_score,
        uncertainty_reason=uncertainty_reason,
        sources=sources,
        verification=verdict,
        reasoning_chain=reasoning_chain,
    )

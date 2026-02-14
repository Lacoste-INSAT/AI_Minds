"""
Synapsis Reasoning Engine - LLM Agent
Synthesizes grounded answers from retrieved context with inline citations.
"""
import json
import logging
import re
import time
from typing import Optional

from .models import (
    AnswerPacket, 
    ChunkEvidence, 
    ConfidenceLevel, 
    FusedContext,
    LLMResponse,
    ModelTier,
    QueryType,
    VerificationVerdict,
)
from .ollama_client import generate_completion
from .fusion import format_context_for_llm


logger = logging.getLogger(__name__)


# System prompt for answer synthesis
REASONING_SYSTEM_PROMPT = """You are a personal knowledge assistant answering questions based ONLY on the user's own documents.

CRITICAL RULES:
1. ONLY use information from the provided sources. Do NOT add external knowledge.
2. If the sources don't contain enough information, say "I don't have enough information in your documents."
3. Cite sources using [Source N] markers inline with your answer.
4. Be concise but complete.
5. If sources conflict, acknowledge the contradiction.

Your response MUST be grounded in the provided context. Never fabricate information."""


# System prompt for the critic agent
CRITIC_SYSTEM_PROMPT = """You are a verification agent. Your job is to check if an answer is properly supported by the sources.

Analyze the answer and sources, then respond with JSON:
{
    "verdict": "APPROVE" | "REVISE" | "REJECT",
    "reasoning": "Brief explanation",
    "unsupported_claims": ["list of claims not found in sources"],
    "suggested_revision": "If REVISE, suggest how to fix"
}

APPROVE: Every claim in the answer is supported by at least one source.
REVISE: Most claims are supported, but some need adjustment.
REJECT: Major claims are fabricated or unsupported."""


def _build_reasoning_prompt(query: str, context: str) -> str:
    """Build the prompt for answer synthesis."""
    return f"""Based on the following sources from the user's documents, answer their question.

SOURCES:
{context}

QUESTION: {query}

Provide a grounded answer with [Source N] citations. If you cannot answer from these sources, say so."""


def _build_critic_prompt(query: str, answer: str, context: str) -> str:
    """Build the prompt for answer verification."""
    return f"""Verify this answer against the sources.

QUESTION: {query}

ANSWER: {answer}

SOURCES:
{context}

Is every claim in the answer supported by the sources? Respond with JSON."""


async def synthesize_answer(
    query: str,
    fused_context: FusedContext,
    query_type: QueryType,
    tier: Optional[ModelTier] = None,
) -> tuple[str, LLMResponse]:
    """
    Call LLM to synthesize an answer from the fused context.
    Returns the answer text and raw LLM response.
    """
    context_str = format_context_for_llm(fused_context)
    prompt = _build_reasoning_prompt(query, context_str)
    
    response = await generate_completion(
        prompt=prompt,
        system_prompt=REASONING_SYSTEM_PROMPT,
        json_mode=False,
        tier=tier or ModelTier.T3,
    )
    
    if response.success:
        return response.content.strip(), response
    else:
        return "", response


async def verify_answer(
    query: str,
    answer: str,
    fused_context: FusedContext,
    tier: Optional[ModelTier] = None,
) -> tuple[VerificationVerdict, str, Optional[str]]:
    """
    Critic agent: verify the answer against sources.
    Returns (verdict, reasoning, suggested_revision).
    """
    context_str = format_context_for_llm(fused_context)
    prompt = _build_critic_prompt(query, answer, context_str)
    
    response = await generate_completion(
        prompt=prompt,
        system_prompt=CRITIC_SYSTEM_PROMPT,
        json_mode=True,
        tier=tier or ModelTier.T3,
    )
    
    if response.success and response.content:
        try:
            result = json.loads(response.content)
            verdict_str = result.get("verdict", "APPROVE").upper()
            
            try:
                verdict = VerificationVerdict(verdict_str)
            except ValueError:
                verdict = VerificationVerdict.APPROVE
            
            reasoning = result.get("reasoning", "")
            revision = result.get("suggested_revision")
            
            return verdict, reasoning, revision
            
        except json.JSONDecodeError:
            logger.warning("Critic returned invalid JSON, defaulting to REVISE")
    
    # Default to REVISE if critic fails - safer than APPROVE for hallucination prevention
    return VerificationVerdict.REVISE, "Verification parsing failed - treating as needs revision", None


def compute_confidence(
    fused_context: FusedContext,
    verification: VerificationVerdict,
) -> tuple[ConfidenceLevel, float, Optional[str]]:
    """
    Compute confidence score based on:
    - Top source score (30%)
    - Source agreement (30%) - approximated by score variance
    - Source count (20%)
    - Recency (20%) - TODO: needs timestamp data
    
    Returns (level, score, uncertainty_reason).
    """
    chunks = fused_context.chunks
    
    if not chunks:
        return ConfidenceLevel.NONE, 0.0, "No relevant sources found"
    
    # Factor 1: Top source score (normalize to 0-1)
    top_score = chunks[0].score_final if chunks else 0.0
    # RRF scores are small, normalize
    top_source_factor = min(1.0, top_score * 10)
    
    # Factor 2: Source agreement (based on score variance)
    # If all sources have similar scores = high agreement
    if len(chunks) >= 2:
        scores = [c.score_final for c in chunks[:5]]
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        # Low variance = high agreement
        agreement_factor = max(0.0, 1.0 - variance * 100)
    else:
        agreement_factor = 0.5  # Neutral with single source
    
    # Factor 3: Source count
    source_count_factor = min(1.0, len(chunks) / 3)
    
    # Factor 4: Recency - DISABLED until timestamps are populated by ingestion
    # Setting weight to 0 and redistributing to other factors for honesty
    # TODO: Enable when ChunkEvidence has timestamp field populated
    recency_factor = 0.5  # Neutral value (not used in calculation)
    
    # Weighted combination (recency disabled - weights redistributed)
    # Original: 0.30 + 0.30 + 0.20 + 0.20 = 1.0
    # Current:  0.40 + 0.35 + 0.25 + 0.00 = 1.0
    confidence_score = (
        0.40 * top_source_factor +
        0.35 * agreement_factor +
        0.25 * source_count_factor
        # + 0.0 * recency_factor  # Disabled until implemented
    )
    
    # Penalize if critic rejected
    if verification == VerificationVerdict.REJECT:
        confidence_score *= 0.3
    elif verification == VerificationVerdict.REVISE:
        confidence_score *= 0.7
    
    # Map to level
    if confidence_score >= 0.7:
        level = ConfidenceLevel.HIGH
        reason = None
    elif confidence_score >= 0.4:
        level = ConfidenceLevel.MEDIUM
        reason = "Moderate source coverage"
    elif confidence_score >= 0.2:
        level = ConfidenceLevel.LOW
        reason = "Limited source support"
    else:
        level = ConfidenceLevel.NONE
        reason = "Insufficient evidence in your documents"
    
    return level, confidence_score, reason


def _generate_abstention_response(
    query: str,
    fused_context: FusedContext,
    reason: str,
) -> str:
    """Generate a graceful abstention response with partial results."""
    response = f"I don't have enough information in your documents to answer this confidently.\n\n"
    response += f"Reason: {reason}\n\n"
    
    if fused_context.chunks:
        response += "Here's what I found that might be related:\n\n"
        for i, chunk in enumerate(fused_context.chunks[:3], start=1):
            snippet = chunk.snippet[:200] + "..." if len(chunk.snippet) > 200 else chunk.snippet
            file_info = f" ({chunk.file_name})" if chunk.file_name else ""
            response += f"- [Source {i}]{file_info}: {snippet}\n\n"
    
    return response


async def reason_and_respond(
    query: str,
    fused_context: FusedContext,
    query_type: QueryType,
    tier: Optional[ModelTier] = None,
    max_retries: int = 1,
) -> AnswerPacket:
    """
    Full reasoning pipeline:
    1. Synthesize answer from context
    2. Verify with critic
    3. Retry if REVISE
    4. Compute confidence
    5. Return final AnswerPacket
    """
    start_time = time.perf_counter()
    tier = tier or ModelTier.T3
    
    # Handle empty context
    if not fused_context.chunks:
        return AnswerPacket(
            answer=_generate_abstention_response(query, fused_context, "No relevant documents found"),
            confidence=ConfidenceLevel.NONE,
            confidence_score=0.0,
            sources=[],
            verification=VerificationVerdict.REJECT,
            query_type=query_type,
            model_used=tier,
            uncertainty_reason="No relevant sources found",
            latency_ms=(time.perf_counter() - start_time) * 1000,
        )
    
    # Step 1: Synthesize answer
    answer, llm_response = await synthesize_answer(query, fused_context, query_type, tier)
    
    if not answer:
        return AnswerPacket(
            answer=_generate_abstention_response(query, fused_context, "Failed to generate response"),
            confidence=ConfidenceLevel.NONE,
            confidence_score=0.0,
            sources=fused_context.chunks,
            verification=VerificationVerdict.REJECT,
            query_type=query_type,
            model_used=tier,
            uncertainty_reason=llm_response.error or "LLM generation failed",
            latency_ms=(time.perf_counter() - start_time) * 1000,
        )
    
    # Step 2: Verify with critic
    verification, critic_reasoning, revision = await verify_answer(
        query, answer, fused_context, tier
    )
    
    # Step 3: Retry if REVISE (up to max_retries)
    retries = 0
    while verification == VerificationVerdict.REVISE and retries < max_retries:
        logger.info(f"Critic suggested revision, retrying... ({retries + 1}/{max_retries})")
        
        # Add revision guidance to the prompt
        revision_prompt = f"Previous answer had issues: {critic_reasoning}\n{revision or ''}\n\nPlease revise."
        answer, llm_response = await synthesize_answer(
            f"{query}\n\n{revision_prompt}", 
            fused_context, 
            query_type, 
            tier
        )
        
        verification, critic_reasoning, revision = await verify_answer(
            query, answer, fused_context, tier
        )
        retries += 1
    
    # Step 4: Compute confidence
    confidence_level, confidence_score, uncertainty_reason = compute_confidence(
        fused_context, verification
    )
    
    # Step 5: Handle low confidence / rejection
    if confidence_level == ConfidenceLevel.NONE or verification == VerificationVerdict.REJECT:
        answer = _generate_abstention_response(
            query, 
            fused_context, 
            uncertainty_reason or "Answer could not be verified"
        )
    
    latency = (time.perf_counter() - start_time) * 1000
    
    return AnswerPacket(
        answer=answer,
        confidence=confidence_level,
        confidence_score=confidence_score,
        sources=fused_context.chunks,
        verification=verification,
        query_type=query_type,
        model_used=tier,
        uncertainty_reason=uncertainty_reason,
        reasoning_chain=critic_reasoning,
        latency_ms=latency,
    )

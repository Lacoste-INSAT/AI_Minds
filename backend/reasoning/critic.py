"""
Critic Agent
============
Verifies LLM answers against source documents.

Verdicts:
- APPROVE: Answer is fully supported by sources
- REVISE: Answer needs adjustment (with feedback)
- REJECT: Answer is fabricated or unsupported

This is our quality gate - prevents hallucinations from reaching users.
"""

import structlog
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import json
import re

from .ollama_client import OllamaClient, ModelTier
from .fusion import FusedResult, build_context_string
from .reasoner import ReasoningResult

logger = structlog.get_logger(__name__)


class CriticVerdict(Enum):
    """Possible verdicts from critic agent."""
    APPROVE = "approve"   # Answer is grounded, send to user
    REVISE = "revise"     # Partially correct, needs adjustment
    REJECT = "reject"     # Fabricated/hallucinated, don't show


@dataclass
class CriticResult:
    """Result from critic verification."""
    verdict: CriticVerdict
    confidence: float  # 0-1, how confident in the verdict
    feedback: str  # Explanation of verdict
    issues_found: list[str]  # Specific issues identified
    claims_verified: int  # Number of claims checked
    claims_supported: int  # Number of claims with source support
    model_used: str


CRITIC_SYSTEM_PROMPT = """You are a verification agent that checks if answers are supported by source documents.

YOUR TASK:
1. Read the question and proposed answer
2. Check each claim in the answer against the sources
3. Determine if the answer is:
   - APPROVE: All claims are supported by the sources
   - REVISE: Some claims are supported but some need correction
   - REJECT: The answer contains fabricated information not in sources

BE STRICT:
- If a claim cannot be verified in the sources, it's unsupported
- If the answer adds information not in sources, mark for REVISE or REJECT
- If the answer contradicts the sources, REJECT

OUTPUT JSON ONLY:
{
    "verdict": "APPROVE|REVISE|REJECT",
    "confidence": 0.0-1.0,
    "feedback": "Explanation of your verdict",
    "issues": ["issue 1", "issue 2"],
    "claims_checked": 5,
    "claims_supported": 4
}"""


CRITIC_USER_TEMPLATE = """Question: {question}

Answer to verify:
{answer}

Sources:
{sources}

Verify if the answer is fully supported by these sources. Output JSON only."""


class CriticAgent:
    """
    Verifies answers against source documents.
    
    Usage:
        critic = CriticAgent(ollama_client)
        result = await critic.verify(
            question="What's the budget?",
            answer="The budget is $50,000 [Source 1]",
            sources=fused_results
        )
        if result.verdict == CriticVerdict.APPROVE:
            # Safe to show to user
    """
    
    def __init__(
        self,
        ollama_client: OllamaClient,
        max_context_chars: int = 6000,
        strict_mode: bool = True,
    ):
        """
        Args:
            ollama_client: Ollama client for LLM calls
            max_context_chars: Max chars for source context
            strict_mode: If True, require explicit source support for all claims
        """
        self.ollama = ollama_client
        self.max_context_chars = max_context_chars
        self.strict_mode = strict_mode
    
    async def verify(
        self,
        question: str,
        answer: str,
        sources: list[FusedResult],
        tier: Optional[ModelTier] = None,
    ) -> CriticResult:
        """
        Verify an answer against sources.
        
        Args:
            question: Original user question
            answer: Generated answer to verify
            sources: Source documents used for the answer
            tier: LLM tier (defaults to T1 for accuracy)
            
        Returns:
            CriticResult with verdict and details
        """
        # Handle empty/abstention cases
        if not answer or not answer.strip():
            return CriticResult(
                verdict=CriticVerdict.APPROVE,
                confidence=1.0,
                feedback="No answer to verify (abstention)",
                issues_found=[],
                claims_verified=0,
                claims_supported=0,
                model_used="none",
            )
        
        if not sources:
            return CriticResult(
                verdict=CriticVerdict.REJECT,
                confidence=1.0,
                feedback="No sources provided to verify against",
                issues_found=["No source documents available"],
                claims_verified=0,
                claims_supported=0,
                model_used="none",
            )
        
        # Build context
        sources_text = build_context_string(sources, self.max_context_chars)
        
        prompt = CRITIC_USER_TEMPLATE.format(
            question=question,
            answer=answer,
            sources=sources_text
        )
        
        try:
            response = await self.ollama.generate(
                prompt=prompt,
                system_prompt=CRITIC_SYSTEM_PROMPT,
                tier=tier or ModelTier.T1,  # Use best model for verification
                temperature=0.0,  # Deterministic
                max_tokens=512,
                json_mode=True,
            )
            
            result = self._parse_response(response.content, response.model_used)
            
            logger.info(
                "critic_verification_complete",
                verdict=result.verdict.value,
                confidence=result.confidence,
                claims_ratio=f"{result.claims_supported}/{result.claims_verified}",
            )
            
            return result
            
        except Exception as e:
            logger.error("critic_verification_failed", error=str(e))
            # On error, be conservative - REVISE not APPROVE
            return CriticResult(
                verdict=CriticVerdict.REVISE,
                confidence=0.3,
                feedback=f"Verification error: {str(e)}. Treating as needs-review.",
                issues_found=["Verification process failed"],
                claims_verified=0,
                claims_supported=0,
                model_used="error",
            )
    
    def _parse_response(self, raw_response: str, model_used: str) -> CriticResult:
        """Parse JSON response from critic LLM."""
        try:
            # Try to parse JSON
            data = json.loads(raw_response)
            
            verdict_map = {
                "APPROVE": CriticVerdict.APPROVE,
                "REVISE": CriticVerdict.REVISE,
                "REJECT": CriticVerdict.REJECT,
            }
            
            verdict_str = data.get("verdict", "REVISE").upper()
            verdict = verdict_map.get(verdict_str, CriticVerdict.REVISE)
            
            return CriticResult(
                verdict=verdict,
                confidence=float(data.get("confidence", 0.5)),
                feedback=data.get("feedback", "No feedback provided"),
                issues_found=data.get("issues", []),
                claims_verified=int(data.get("claims_checked", 0)),
                claims_supported=int(data.get("claims_supported", 0)),
                model_used=model_used,
            )
            
        except json.JSONDecodeError:
            # Try to extract verdict from text
            verdict = CriticVerdict.REVISE
            raw_upper = raw_response.upper()
            
            if "APPROVE" in raw_upper:
                verdict = CriticVerdict.APPROVE
            elif "REJECT" in raw_upper:
                verdict = CriticVerdict.REJECT
            
            return CriticResult(
                verdict=verdict,
                confidence=0.4,
                feedback=raw_response[:500],
                issues_found=["Could not parse structured response"],
                claims_verified=0,
                claims_supported=0,
                model_used=model_used,
            )
    
    async def quick_check(
        self,
        answer: str,
        sources: list[FusedResult],
    ) -> bool:
        """
        Fast heuristic check (no LLM call).
        
        Returns True if answer looks grounded (has citations that exist in sources).
        This is for quick pre-filtering before full verification.
        """
        if not answer or not sources:
            return False
        
        # Check if answer has citations
        cited_nums = [int(n) for n in re.findall(r'\[Source (\d+)\]', answer)]
        
        if not cited_nums:
            # No citations = suspicious
            return False
        
        # Check if cited sources are valid
        max_source = len(sources)
        valid_citations = all(1 <= n <= max_source for n in cited_nums)
        
        if not valid_citations:
            return False
        
        # Check if cited content appears in answer (rough match)
        answer_lower = answer.lower()
        matches = 0
        for num in cited_nums[:3]:  # Check first 3 citations
            source_content = sources[num - 1].content.lower()
            # Look for keyword overlap
            source_words = set(source_content.split()[:50])
            answer_words = set(answer_lower.split())
            overlap = len(source_words & answer_words)
            if overlap >= 3:
                matches += 1
        
        return matches >= 1


class ReasoningPipeline:
    """
    Full reasoning pipeline with critic verification loop.
    
    Orchestrates: Query Planning → Retrieval → Reasoning → Verification
    With automatic retry on REVISE verdict.
    """
    
    def __init__(
        self,
        ollama_client: OllamaClient,
        retriever,  # HybridRetriever
        max_revisions: int = 1,
    ):
        from .query_planner import QueryPlanner
        from .reasoner import LLMReasoner
        from .fusion import RRFFusion
        
        self.ollama = ollama_client
        self.retriever = retriever
        self.planner = QueryPlanner(ollama_client)
        self.reasoner = LLMReasoner(ollama_client)
        self.critic = CriticAgent(ollama_client)
        self.fusion = RRFFusion(k=60, recency_weight=0.1)
        self.max_revisions = max_revisions
    
    async def answer(self, question: str) -> dict:
        """
        Full pipeline from question to verified answer.
        
        Returns:
            {
                "answer": str,
                "sources": list,
                "confidence": str,
                "verdict": str,
                "reasoning": str,
                "metadata": dict
            }
        """
        from .confidence import ConfidenceScorer, ConfidenceLevel
        
        # Step 1: Plan query
        plan = await self.planner.plan(question)
        strategy = self.planner.get_retrieval_strategy(plan)
        
        logger.info(
            "pipeline_query_planned",
            query_type=plan.query_type.value,
            entities=plan.entities_mentioned,
        )
        
        # Step 2: Retrieve
        bundle = await self.retriever.search(
            query=question,
            entities=plan.entities_mentioned,
            dense_k=strategy["dense_k"],
            sparse_k=strategy["sparse_k"],
            graph_hops=strategy["graph_hops"],
        )
        
        # Step 3: Fuse results
        fused = self.fusion.fuse(
            bundle,
            top_k=10,
            temporal_sort=strategy["temporal_sort"],
        )
        
        if not fused:
            return {
                "answer": "I don't have any relevant information in your records to answer this.",
                "sources": [],
                "confidence": "none",
                "verdict": "abstain",
                "reasoning": "No relevant sources found",
                "metadata": {"query_type": plan.query_type.value}
            }
        
        # Step 4: Reason
        reasoning_result = await self.reasoner.reason(question, fused)
        
        if reasoning_result.abstained:
            return {
                "answer": reasoning_result.answer,
                "sources": [],
                "confidence": "none",
                "verdict": "abstain",
                "reasoning": reasoning_result.abstention_reason or "Insufficient information",
                "metadata": {"query_type": plan.query_type.value}
            }
        
        # Step 5: Verify with critic
        critic_result = await self.critic.verify(
            question=question,
            answer=reasoning_result.answer,
            sources=fused,
        )
        
        # Step 6: Handle REVISE verdict (one retry)
        revisions = 0
        while critic_result.verdict == CriticVerdict.REVISE and revisions < self.max_revisions:
            logger.info("pipeline_revising", feedback=critic_result.feedback)
            
            reasoning_result = await self.reasoner.reason_with_followup(
                question=question,
                sources=fused,
                previous_answer=reasoning_result.answer,
                feedback=critic_result.feedback,
            )
            
            critic_result = await self.critic.verify(
                question=question,
                answer=reasoning_result.answer,
                sources=fused,
            )
            revisions += 1
        
        # Step 7: Calculate final confidence
        scorer = ConfidenceScorer()
        confidence = scorer.calculate(
            retrieval_results=fused,
            reasoning_result=reasoning_result,
            critic_result=critic_result,
        )
        
        # Step 8: Handle REJECT verdict
        if critic_result.verdict == CriticVerdict.REJECT:
            return {
                "answer": "I found some information but couldn't verify it well enough. Here's what I found with low confidence:\n\n" + reasoning_result.answer,
                "sources": reasoning_result.citations,
                "confidence": "low",
                "verdict": "rejected",
                "reasoning": critic_result.feedback,
                "metadata": {
                    "query_type": plan.query_type.value,
                    "issues": critic_result.issues_found,
                }
            }
        
        return {
            "answer": reasoning_result.answer,
            "sources": reasoning_result.citations,
            "confidence": confidence.level.value,
            "verdict": critic_result.verdict.value,
            "reasoning": reasoning_result.reasoning_chain,
            "metadata": {
                "query_type": plan.query_type.value,
                "model": reasoning_result.model_used,
                "sources_used": len(reasoning_result.sources_used),
                "contradictions": reasoning_result.contradictions_found,
                "confidence_score": confidence.score,
            }
        }

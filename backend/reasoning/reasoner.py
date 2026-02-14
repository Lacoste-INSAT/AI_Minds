"""
LLM Reasoner
============
Synthesizes grounded answers from retrieved context with inline citations.

Key features:
- Inline source citations [Source 1], [Source 2]
- Reasoning transparency (shows chain-of-thought)
- Handles contradictions in sources
- Abstains when context insufficient
"""

import structlog
from dataclasses import dataclass, field
from typing import Optional
import json
import re

from .ollama_client import OllamaClient, ModelTier
from .fusion import FusedResult, build_context_string

logger = structlog.get_logger(__name__)


@dataclass
class ReasoningResult:
    """Result from LLM reasoning step."""
    answer: str
    citations: list[dict]  # [{"source_num": 1, "text": "...", "file": "..."}]
    reasoning_chain: str  # How the answer was derived
    sources_used: list[int]  # Which source numbers were cited
    model_used: str
    raw_response: str
    abstained: bool = False
    abstention_reason: Optional[str] = None
    contradictions_found: list[str] = field(default_factory=list)


REASONER_SYSTEM_PROMPT = """You are a knowledge assistant that answers questions using ONLY the provided sources.

CRITICAL RULES:
1. ONLY use information from the provided sources. Never use outside knowledge.
2. Cite sources inline using [Source N] format where N is the source number.
3. If sources contradict each other, acknowledge the contradiction and cite both.
4. If sources don't contain enough information to answer, say so clearly.
5. Be concise but complete.

FORMAT YOUR RESPONSE AS:
<reasoning>
Your step-by-step reasoning about how to answer using the sources.
</reasoning>

<answer>
Your answer with inline [Source N] citations.
</answer>

<contradictions>
List any contradictions found between sources (or "None" if no contradictions).
</contradictions>

If you cannot answer from the sources, use:
<abstain>
Reason why you cannot answer.
</abstain>"""


REASONER_USER_TEMPLATE = """Question: {question}

Sources:
{context}

Based ONLY on the sources above, answer the question with inline citations."""


class LLMReasoner:
    """
    Synthesizes answers from retrieved context with citations.
    
    Usage:
        reasoner = LLMReasoner(ollama_client)
        result = await reasoner.reason(
            question="What did Sarah say about the budget?",
            sources=fused_results
        )
        print(result.answer)  # "Sarah mentioned [Source 1] that the budget..."
    """
    
    def __init__(
        self,
        ollama_client: OllamaClient,
        max_context_chars: int = 8000,
    ):
        self.ollama = ollama_client
        self.max_context_chars = max_context_chars
    
    async def reason(
        self,
        question: str,
        sources: list[FusedResult],
        tier: Optional[ModelTier] = None,
    ) -> ReasoningResult:
        """
        Generate a grounded answer with citations.
        
        Args:
            question: User's question
            sources: Fused retrieval results
            tier: LLM tier to use (defaults to T1)
            
        Returns:
            ReasoningResult with answer, citations, reasoning chain
        """
        # Build context from sources
        context = build_context_string(sources, self.max_context_chars)
        
        # Check if we have any context
        if not context.strip():
            return ReasoningResult(
                answer="I don't have any relevant information in your records to answer this question.",
                citations=[],
                reasoning_chain="No sources retrieved",
                sources_used=[],
                model_used="none",
                raw_response="",
                abstained=True,
                abstention_reason="No relevant sources found"
            )
        
        # Build prompt
        prompt = REASONER_USER_TEMPLATE.format(
            question=question,
            context=context
        )
        
        try:
            response = await self.ollama.generate(
                prompt=prompt,
                system_prompt=REASONER_SYSTEM_PROMPT,
                tier=tier,
                temperature=0.1,  # Low temp for factuality
                max_tokens=2048,
            )
            
            # Parse the structured response
            result = self._parse_response(response.content, sources, response.model_used)
            
            logger.info(
                "reasoning_complete",
                question=question[:50],
                sources_used=result.sources_used,
                abstained=result.abstained,
                model=result.model_used,
            )
            
            return result
            
        except Exception as e:
            logger.error("reasoning_failed", error=str(e))
            return ReasoningResult(
                answer="I encountered an error while processing your question. Please try again.",
                citations=[],
                reasoning_chain=f"Error: {str(e)}",
                sources_used=[],
                model_used="error",
                raw_response="",
                abstained=True,
                abstention_reason=f"Processing error: {str(e)}"
            )
    
    def _parse_response(
        self,
        raw_response: str,
        sources: list[FusedResult],
        model_used: str,
    ) -> ReasoningResult:
        """Parse the structured LLM response."""
        
        # Extract sections using regex
        reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', raw_response, re.DOTALL)
        answer_match = re.search(r'<answer>(.*?)</answer>', raw_response, re.DOTALL)
        contradictions_match = re.search(r'<contradictions>(.*?)</contradictions>', raw_response, re.DOTALL)
        abstain_match = re.search(r'<abstain>(.*?)</abstain>', raw_response, re.DOTALL)
        
        # Handle abstention
        if abstain_match:
            return ReasoningResult(
                answer="I don't have enough information in your records to answer this confidently.",
                citations=[],
                reasoning_chain=abstain_match.group(1).strip(),
                sources_used=[],
                model_used=model_used,
                raw_response=raw_response,
                abstained=True,
                abstention_reason=abstain_match.group(1).strip()
            )
        
        # Extract answer (fallback to full response if no tags)
        answer = ""
        if answer_match:
            answer = answer_match.group(1).strip()
        else:
            # Try to extract without tags
            answer = raw_response.strip()
        
        # Extract reasoning
        reasoning = ""
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        
        # Extract contradictions
        contradictions = []
        if contradictions_match:
            cont_text = contradictions_match.group(1).strip()
            if cont_text.lower() != "none" and cont_text:
                # Split by lines or bullet points
                contradictions = [c.strip() for c in re.split(r'[\n\-•]', cont_text) if c.strip()]
        
        # Extract cited source numbers from answer
        source_nums = list(set(int(n) for n in re.findall(r'\[Source (\d+)\]', answer)))
        
        # Build citations list with actual source details
        citations = []
        for num in source_nums:
            if 0 < num <= len(sources):
                source = sources[num - 1]
                citations.append({
                    "source_num": num,
                    "file": source.source_file,
                    "label": source.citation_label,
                    "snippet": source.content[:200] + "..." if len(source.content) > 200 else source.content,
                })
        
        return ReasoningResult(
            answer=answer,
            citations=citations,
            reasoning_chain=reasoning,
            sources_used=source_nums,
            model_used=model_used,
            raw_response=raw_response,
            abstained=False,
            contradictions_found=contradictions,
        )
    
    async def reason_with_followup(
        self,
        question: str,
        sources: list[FusedResult],
        previous_answer: str,
        feedback: str,
        tier: Optional[ModelTier] = None,
    ) -> ReasoningResult:
        """
        Re-reason with feedback (used after critic REVISE verdict).
        
        Args:
            question: Original question
            sources: Retrieved sources
            previous_answer: The answer that needed revision
            feedback: Critic's feedback on what to fix
            tier: LLM tier
            
        Returns:
            Revised ReasoningResult
        """
        context = build_context_string(sources, self.max_context_chars)
        
        followup_prompt = f"""Question: {question}

Sources:
{context}

Your previous answer: {previous_answer}

Feedback: {feedback}

Please revise your answer addressing the feedback. Use ONLY the sources provided.
Cite sources inline using [Source N] format."""

        try:
            response = await self.ollama.generate(
                prompt=followup_prompt,
                system_prompt=REASONER_SYSTEM_PROMPT,
                tier=tier,
                temperature=0.1,
                max_tokens=2048,
            )
            
            return self._parse_response(response.content, sources, response.model_used)
            
        except Exception as e:
            logger.error("followup_reasoning_failed", error=str(e))
            return ReasoningResult(
                answer=previous_answer,  # Fall back to previous
                citations=[],
                reasoning_chain=f"Revision failed: {str(e)}",
                sources_used=[],
                model_used="error",
                raw_response="",
            )


def format_answer_for_display(result: ReasoningResult) -> dict:
    """
    Format reasoning result for frontend display.
    
    Returns dict with:
    - answer_html: Answer with clickable citation links
    - sources: List of source details for sidebar
    - confidence_context: Info for confidence badge
    """
    
    # Convert [Source N] to HTML links
    answer_html = result.answer
    for citation in result.citations:
        num = citation["source_num"]
        # Replace with styled citation
        answer_html = answer_html.replace(
            f"[Source {num}]",
            f'<cite data-source="{num}">[{num}]</cite>'
        )
    
    return {
        "answer_html": answer_html,
        "answer_plain": result.answer,
        "sources": result.citations,
        "reasoning": result.reasoning_chain,
        "sources_count": len(result.sources_used),
        "model": result.model_used,
        "abstained": result.abstained,
        "abstention_reason": result.abstention_reason,
        "contradictions": result.contradictions_found,
    }

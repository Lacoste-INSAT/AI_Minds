"""
Confidence Scorer
=================
Calculates confidence levels for answers based on multiple signals.

Formula (from ARCHITECTURE.md):
confidence = 0.3 * top_source_score 
           + 0.3 * source_agreement 
           + 0.2 * source_count_factor 
           + 0.2 * recency_factor

Levels:
- HIGH (≥0.7): Strong source support, can trust answer
- MEDIUM (≥0.4): Decent support, some uncertainty  
- LOW (≥0.2): Weak support, treat with caution
- NONE (<0.2): Insufficient support, trigger abstention
"""

import structlog
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta

logger = structlog.get_logger(__name__)


class ConfidenceLevel(Enum):
    """Confidence levels for answers."""
    HIGH = "high"      # ≥0.7 - Strong support
    MEDIUM = "medium"  # ≥0.4 - Some uncertainty
    LOW = "low"        # ≥0.2 - Treat with caution
    NONE = "none"      # <0.2 - Abstain


@dataclass
class ConfidenceResult:
    """Detailed confidence calculation result."""
    level: ConfidenceLevel
    score: float  # Raw score 0-1
    breakdown: dict  # Individual factor scores
    reasoning: str  # Human-readable explanation
    should_abstain: bool  # If True, answer should be withheld


class ConfidenceScorer:
    """
    Calculates answer confidence from multiple signals.
    
    Signals:
    1. Top source score - How relevant is the best source?
    2. Source agreement - Do sources agree or contradict?
    3. Source count - How many sources support the answer?
    4. Recency - How recent are the sources?
    5. Critic verdict - Did the critic approve?
    
    Usage:
        scorer = ConfidenceScorer()
        result = scorer.calculate(
            retrieval_results=fused_results,
            reasoning_result=reasoning_result,
            critic_result=critic_result
        )
        print(f"Confidence: {result.level.value} ({result.score:.2f})")
    """
    
    def __init__(
        self,
        weights: Optional[dict] = None,
        thresholds: Optional[dict] = None,
    ):
        """
        Args:
            weights: Custom weights for each factor
            thresholds: Custom thresholds for confidence levels
        """
        self.weights = weights or {
            "top_source": 0.25,
            "source_agreement": 0.25,
            "source_count": 0.20,
            "recency": 0.15,
            "critic": 0.15,
        }
        
        self.thresholds = thresholds or {
            ConfidenceLevel.HIGH: 0.70,
            ConfidenceLevel.MEDIUM: 0.40,
            ConfidenceLevel.LOW: 0.20,
        }
    
    def calculate(
        self,
        retrieval_results: list,
        reasoning_result=None,
        critic_result=None,
    ) -> ConfidenceResult:
        """
        Calculate confidence score for an answer.
        
        Args:
            retrieval_results: List of FusedResult from retrieval
            reasoning_result: ReasoningResult from reasoner
            critic_result: CriticResult from verification
            
        Returns:
            ConfidenceResult with level, score, and breakdown
        """
        breakdown = {}
        
        # Factor 1: Top source score (0-1)
        if retrieval_results:
            top_score = max(r.fused_score for r in retrieval_results)
            # Normalize (fused scores are typically small)
            breakdown["top_source"] = min(top_score * 10, 1.0)
        else:
            breakdown["top_source"] = 0.0
        
        # Factor 2: Source agreement (0-1)
        breakdown["source_agreement"] = self._calculate_agreement(reasoning_result)
        
        # Factor 3: Source count factor
        # min(count / 3, 1.0) - having 3+ sources gives full score
        if reasoning_result and reasoning_result.sources_used:
            count = len(reasoning_result.sources_used)
            breakdown["source_count"] = min(count / 3.0, 1.0)
        elif retrieval_results:
            breakdown["source_count"] = min(len(retrieval_results) / 3.0, 1.0)
        else:
            breakdown["source_count"] = 0.0
        
        # Factor 4: Recency factor
        breakdown["recency"] = self._calculate_recency(retrieval_results)
        
        # Factor 5: Critic verdict
        breakdown["critic"] = self._calculate_critic_score(critic_result)
        
        # Calculate weighted score
        score = sum(
            self.weights[factor] * breakdown[factor]
            for factor in self.weights
        )
        
        # Determine level
        level = self._score_to_level(score)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(breakdown, level)
        
        # Should abstain if NONE confidence
        should_abstain = level == ConfidenceLevel.NONE
        
        logger.info(
            "confidence_calculated",
            level=level.value,
            score=round(score, 3),
            breakdown={k: round(v, 3) for k, v in breakdown.items()}
        )
        
        return ConfidenceResult(
            level=level,
            score=score,
            breakdown=breakdown,
            reasoning=reasoning,
            should_abstain=should_abstain,
        )
    
    def _calculate_agreement(self, reasoning_result) -> float:
        """
        Calculate source agreement factor.
        
        0 = contradictions found
        0.5 = some uncertainty
        1 = unanimous agreement
        """
        if not reasoning_result:
            return 0.5
        
        # Check for contradictions
        if hasattr(reasoning_result, 'contradictions_found'):
            contradictions = reasoning_result.contradictions_found
            if contradictions and len(contradictions) > 0:
                # More contradictions = lower agreement
                return max(0.0, 1.0 - len(contradictions) * 0.25)
        
        # If we have multiple sources and no contradictions, good agreement
        if hasattr(reasoning_result, 'sources_used'):
            if len(reasoning_result.sources_used) >= 2:
                return 1.0
            elif len(reasoning_result.sources_used) == 1:
                return 0.7  # Single source, can't measure agreement
        
        return 0.5
    
    def _calculate_recency(self, retrieval_results: list) -> float:
        """
        Calculate recency factor based on source dates.
        
        Uses exponential decay: recent = higher score.
        """
        if not retrieval_results:
            return 0.5
        
        now = datetime.now()
        recency_scores = []
        
        for result in retrieval_results[:5]:  # Check top 5
            metadata = getattr(result, 'metadata', {}) or {}
            created_at = metadata.get('created_at')
            
            if not created_at:
                recency_scores.append(0.5)
                continue
            
            try:
                if isinstance(created_at, str):
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if dt.tzinfo:
                        dt = dt.replace(tzinfo=None)
                else:
                    dt = created_at
                
                age_days = (now - dt).days
                # Exponential decay: halflife of 30 days
                score = 0.5 ** (age_days / 30)
                recency_scores.append(score)
                
            except Exception:
                recency_scores.append(0.5)
        
        return sum(recency_scores) / len(recency_scores) if recency_scores else 0.5
    
    def _calculate_critic_score(self, critic_result) -> float:
        """
        Calculate critic factor from verification result.
        
        APPROVE = 1.0
        REVISE = 0.5
        REJECT = 0.0
        """
        if not critic_result:
            return 0.5  # No verification = neutral
        
        from .critic import CriticVerdict
        
        verdict_scores = {
            CriticVerdict.APPROVE: 1.0,
            CriticVerdict.REVISE: 0.5,
            CriticVerdict.REJECT: 0.0,
        }
        
        return verdict_scores.get(critic_result.verdict, 0.5)
    
    def _score_to_level(self, score: float) -> ConfidenceLevel:
        """Convert numeric score to confidence level."""
        if score >= self.thresholds[ConfidenceLevel.HIGH]:
            return ConfidenceLevel.HIGH
        elif score >= self.thresholds[ConfidenceLevel.MEDIUM]:
            return ConfidenceLevel.MEDIUM
        elif score >= self.thresholds[ConfidenceLevel.LOW]:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.NONE
    
    def _generate_reasoning(self, breakdown: dict, level: ConfidenceLevel) -> str:
        """Generate human-readable confidence explanation."""
        parts = []
        
        # Top source quality
        if breakdown["top_source"] >= 0.7:
            parts.append("highly relevant sources found")
        elif breakdown["top_source"] >= 0.4:
            parts.append("moderately relevant sources")
        else:
            parts.append("weak source relevance")
        
        # Source count
        count_score = breakdown["source_count"]
        if count_score >= 1.0:
            parts.append("multiple supporting sources")
        elif count_score >= 0.5:
            parts.append("limited sources")
        else:
            parts.append("few sources")
        
        # Agreement
        if breakdown["source_agreement"] >= 0.8:
            parts.append("sources agree")
        elif breakdown["source_agreement"] < 0.5:
            parts.append("some contradictions")
        
        # Critic
        if breakdown["critic"] >= 0.8:
            parts.append("verified by critic")
        elif breakdown["critic"] < 0.5:
            parts.append("verification concerns")
        
        # Overall
        level_text = {
            ConfidenceLevel.HIGH: "High confidence",
            ConfidenceLevel.MEDIUM: "Medium confidence",
            ConfidenceLevel.LOW: "Low confidence",
            ConfidenceLevel.NONE: "Insufficient confidence",
        }
        
        return f"{level_text[level]}: {', '.join(parts)}."


def format_confidence_badge(confidence: ConfidenceResult) -> dict:
    """
    Format confidence for frontend display.
    
    Returns dict suitable for rendering a confidence badge.
    """
    colors = {
        ConfidenceLevel.HIGH: "#22c55e",   # Green
        ConfidenceLevel.MEDIUM: "#eab308", # Yellow
        ConfidenceLevel.LOW: "#f97316",    # Orange
        ConfidenceLevel.NONE: "#ef4444",   # Red
    }
    
    labels = {
        ConfidenceLevel.HIGH: "High Confidence",
        ConfidenceLevel.MEDIUM: "Medium Confidence",
        ConfidenceLevel.LOW: "Low Confidence",
        ConfidenceLevel.NONE: "Unverified",
    }
    
    icons = {
        ConfidenceLevel.HIGH: "✓✓",
        ConfidenceLevel.MEDIUM: "✓",
        ConfidenceLevel.LOW: "?",
        ConfidenceLevel.NONE: "✗",
    }
    
    return {
        "level": confidence.level.value,
        "score": round(confidence.score, 2),
        "label": labels[confidence.level],
        "color": colors[confidence.level],
        "icon": icons[confidence.level],
        "tooltip": confidence.reasoning,
        "breakdown": {k: round(v, 2) for k, v in confidence.breakdown.items()},
    }

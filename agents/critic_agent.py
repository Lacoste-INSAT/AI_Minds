"""
SciAgents-inspired Critic Agent

Evaluates hypotheses for scientific rigor and provides revision guidance.
"""
import json
from typing import AsyncIterator

from .base_agent import BaseAgent, AgentResult
from .critic_input import prepare_critic_input
from .confidence import calculate_critic_confidence


class CriticAgent(BaseAgent):
    """Critic Agent - Scientific Quality Control."""
    name = "critic"

    async def run(self, state: dict) -> AgentResult:
        """Main critic execution."""
        hypothesis = state.get("hypothesis", {})
        planner_output = state.get("planner_output", {})
        iteration = state.get("iteration", 1)

        if not hypothesis:
            return self._result({"error": "No hypothesis provided"}, confidence=0.0)

        subgraph = planner_output.get("subgraph", {})
        critic_input = prepare_critic_input(
            hypothesis=hypothesis, subgraph=subgraph,
            kg_metadata=planner_output.get("kg_metadata", {}), iteration=iteration
        )

        try:
            response = await self._ask("critic", critic_input)
            evaluation = self._validate_and_enhance(response, hypothesis, subgraph)
        except Exception as e:
            return self._result({"error": f"Evaluation failed: {e}"}, confidence=0.0)

        return self._result(evaluation, confidence=calculate_critic_confidence(evaluation))

    async def run_stream(self, state: dict) -> AsyncIterator[str]:
        """Stream evaluation in real-time."""
        hypothesis = state.get("hypothesis", {})
        planner_output = state.get("planner_output", {})

        if not hypothesis:
            yield json.dumps({"error": "No hypothesis provided"})
            return

        critic_input = prepare_critic_input(
            hypothesis=hypothesis, subgraph=planner_output.get("subgraph", {}),
            kg_metadata=planner_output.get("kg_metadata", {}),
            iteration=state.get("iteration", 1)
        )

        async for chunk in self._ask_stream("critic", critic_input):
            yield chunk

    def _validate_and_enhance(self, response: dict, hypothesis: dict, subgraph: dict) -> dict:
        """Validate LLM response and add computed metrics."""
        if "decision" not in response:
            scores = response.get("scores", {})
            # Handle case where scores is a list instead of dict
            if isinstance(scores, list):
                scores = {}
            overall = scores.get("overall", {}) if isinstance(scores, dict) else {}
            score = overall.get("score", 5) if isinstance(overall, dict) else 5
            response["decision"] = "APPROVE" if score >= 7 else ("REVISE" if score >= 5 else "REJECT")

        edges = subgraph.get("edges", [])
        if edges:
            avg_conf = sum(e.get("strength", 0.5) for e in edges) / len(edges)
            response["computed_metrics"] = {
                "avg_edge_confidence": round(avg_conf, 3),
                "total_edges": len(edges), "total_nodes": len(subgraph.get("nodes", []))
            }

        response["_metadata"] = {"agent": "critic", "framework": "SciAgents-evaluation"}
        return response

    def should_continue_iteration(self, evaluation: dict, max_iters: int = 3, current: int = 1) -> bool:
        """Determine if another revision iteration is needed."""
        decision = evaluation.get("decision", "REVISE")
        if decision == "APPROVE":
            return False
        return current < max_iters

    def get_revision_guidance(self, evaluation: dict) -> dict:
        """Extract structured revision guidance from evaluation."""
        weaknesses = evaluation.get("weaknesses", [])
        scores = evaluation.get("scores", {})
        # Handle case where scores/weaknesses are not the expected types
        if not isinstance(scores, dict):
            scores = {}
        if not isinstance(weaknesses, list):
            weaknesses = []
        
        return {
            "required_revisions": evaluation.get("required_revisions", []),
            "improvement_suggestions": evaluation.get("improvement_suggestions", []),
            "weaknesses_to_address": [
                w for w in weaknesses
                if isinstance(w, dict) and w.get("severity") in ["critical", "major"]
            ],
            "focus_areas": [
                cat for cat, data in scores.items()
                if isinstance(data, dict) and data.get("score", 10) < 6
            ]
        }

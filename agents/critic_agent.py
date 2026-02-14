"""
Critic Agent — Self-Verification for AI MINDS.

Evaluates whether a generated answer is actually grounded in the
retrieved sources. Decisions: APPROVE / REVISE / REJECT.

This is the differentiator: most chatbots just trust their output.
We verify BEFORE showing the user.
"""

import json
import logging
from typing import AsyncIterator

from agents.base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class CriticAgent(BaseAgent):
    name = "critic"

    async def run(self, state: dict) -> AgentResult:
        question = state.get("question", "")
        answer = state.get("answer", "")
        sources = state.get("sources", [])

        if not answer:
            return self._result({"decision": "REJECT", "reasoning": "No answer to evaluate."}, confidence=0.0)

        # Build critic prompt
        from prompts.loader import load_prompt
        from providers.factory import get_provider

        try:
            system_prompt = load_prompt("critic")
        except FileNotFoundError:
            # Inline fallback if prompt file missing
            system_prompt = (
                "You are a strict fact-checker. Given a QUESTION, an ANSWER, and SOURCE documents, "
                "determine if the answer is grounded in the sources.\n"
                "Respond with JSON: {\"decision\": \"APPROVE|REVISE|REJECT\", \"reasoning\": \"...\"}\n"
                "APPROVE = answer is correct and supported by sources.\n"
                "REVISE  = answer has some basis but contains unsupported claims or errors.\n"
                "REJECT  = answer is not supported by sources or is fabricated."
            )

        sources_text = "\n\n".join(f"[Source {i+1}]: {s}" for i, s in enumerate(sources))

        user_msg = (
            f"QUESTION: {question}\n\n"
            f"ANSWER TO VERIFY:\n{answer}\n\n"
            f"SOURCES:\n{sources_text}"
        )

        provider = get_provider()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ]

        try:
            raw = await provider.generate(messages)
            content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")

            parsed = self._extract_json(content, "critic")
            decision = parsed.get("decision", "REVISE").upper()
            if decision not in ("APPROVE", "REVISE", "REJECT"):
                decision = "REVISE"

            reasoning = parsed.get("reasoning", "")
            confidence = {"APPROVE": 0.9, "REVISE": 0.5, "REJECT": 0.2}.get(decision, 0.5)

            return self._result(
                {"decision": decision, "reasoning": reasoning},
                confidence=confidence,
            )
        except Exception as e:
            logger.warning(f"Critic evaluation failed: {e}")
            return self._result(
                {"decision": "REVISE", "reasoning": f"Critic could not evaluate: {e}"},
                confidence=0.4,
            )

    async def run_stream(self, state: dict) -> AsyncIterator[str]:
        result = await self.run(state)
        yield json.dumps(result.output)

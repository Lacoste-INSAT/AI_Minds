"""
QA Agent — The core brain of AI MINDS.

Flow:
  1. Embed the user's question
  2. Retrieve top-k relevant chunks from Qdrant
  3. Build an augmented prompt with source citations
  4. Generate answer via Ollama (Qwen2.5-3B)
  5. Optionally run the Critic to verify the answer
  6. Return answer + citations + confidence + verification status
"""

import json
import logging
from typing import AsyncIterator

from agents.base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class QAAgent(BaseAgent):
    name = "qa"

    async def run(self, state: dict) -> AgentResult:
        question = state["question"]
        top_k = state.get("top_k", 5)
        verify = state.get("verify", True)

        # --- 1. Retrieve ---
        chunks = self._retrieve(question, top_k)

        if not chunks:
            return self._result(
                {
                    "answer": "I don't have any stored knowledge relevant to this question yet. Try ingesting some files first.",
                    "citations": [],
                    "verification": "NO_CONTEXT",
                    "reasoning": "No relevant chunks found in memory.",
                },
                confidence=0.0,
            )

        # --- 2. Build augmented prompt ---
        context_block = self._build_context(chunks)
        citations = [
            {"source": c["source_file"], "chunk": c["content"][:120], "score": c["score"]}
            for c in chunks
        ]

        # --- 3. Generate answer ---
        from providers.factory import get_provider

        provider = get_provider()
        from prompts.loader import load_prompt

        system_prompt = load_prompt("qa")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"CONTEXT:\n{context_block}\n\nQUESTION: {question}"},
        ]

        raw = await provider.generate(messages)
        answer = raw.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not answer:
            return self._result(
                {"answer": "Failed to generate an answer.", "citations": citations, "verification": "ERROR"},
                confidence=0.0,
            )

        # --- 4. Compute retrieval confidence ---
        avg_score = sum(c["score"] for c in chunks) / len(chunks) if chunks else 0
        top_score = chunks[0]["score"] if chunks else 0
        confidence = round(0.4 * top_score + 0.6 * avg_score, 3)

        # --- 5. Verify with critic ---
        verification = "SKIPPED"
        reasoning = None

        if verify:
            try:
                from agents.critic_agent import CriticAgent
                critic = CriticAgent()
                critic_result = await critic.run({
                    "question": question,
                    "answer": answer,
                    "sources": [c["content"] for c in chunks],
                })
                verification = critic_result.output.get("decision", "UNKNOWN")
                reasoning = critic_result.output.get("reasoning", "")

                # If REVISE, re-generate once with feedback
                if verification == "REVISE" and reasoning:
                    messages.append({"role": "assistant", "content": answer})
                    messages.append({
                        "role": "user",
                        "content": f"A reviewer found issues: {reasoning}\nPlease revise your answer. Stay grounded in the sources.",
                    })
                    raw2 = await provider.generate(messages)
                    revised = raw2.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if revised:
                        answer = revised
                        verification = "REVISED"
            except Exception as e:
                logger.warning(f"Critic failed: {e}")
                verification = "CRITIC_ERROR"

        return self._result(
            {
                "answer": answer,
                "citations": citations,
                "verification": verification,
                "reasoning": reasoning,
            },
            confidence=confidence,
        )

    async def run_stream(self, state: dict) -> AsyncIterator[str]:
        """Stream answer tokens (no critic verification in streaming mode)."""
        question = state["question"]
        top_k = state.get("top_k", 5)

        chunks = self._retrieve(question, top_k)
        context_block = self._build_context(chunks) if chunks else "(No relevant memory found.)"

        from providers.factory import get_provider
        from prompts.loader import load_prompt

        provider = get_provider()
        system_prompt = load_prompt("qa")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"CONTEXT:\n{context_block}\n\nQUESTION: {question}"},
        ]
        async for chunk in provider.stream(messages):
            yield chunk

    # ------------------------------------------------------------------
    def _retrieve(self, question: str, top_k: int) -> list[dict]:
        from encoders.embedder import Embedder
        from retrieval.qdrant_store import QdrantStore
        from config.settings import settings

        embedder = Embedder()
        store = QdrantStore(
            url=settings.qdrant_url,
            collection=settings.qdrant_collection,
            dimension=settings.embedding_dimension,
        )
        vector = embedder.encode(question)
        return store.search(vector, limit=top_k)

    def _build_context(self, chunks: list[dict]) -> str:
        parts = []
        for i, c in enumerate(chunks, 1):
            source = c.get("source_file", "unknown")
            score = c.get("score", 0)
            text = c.get("content", "")
            parts.append(f"[Source {i}: {source} | relevance={score:.2f}]\n{text}")
        return "\n\n---\n\n".join(parts)

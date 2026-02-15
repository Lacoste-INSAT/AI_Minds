"""
Lane-aware model router.
GPU lane handles interactive-heavy tasks; CPU lane handles background tasks.
"""

from __future__ import annotations

from enum import Enum
from typing import AsyncGenerator

import structlog

from backend.config import settings
from backend.services.ollama_client import ollama_client
from backend.services.runtime_incidents import emit_incident

logger = structlog.get_logger(__name__)


class ModelTask(str, Enum):
    interactive_heavy = "interactive_heavy"
    background_enrichment = "background_enrichment"
    background_proactive = "background_proactive"
    classification_light = "classification_light"


class ModelLane(str, Enum):
    gpu = "gpu"
    cpu = "cpu"


TASK_LANE: dict[ModelTask, ModelLane] = {
    ModelTask.interactive_heavy: ModelLane.gpu,
    ModelTask.background_enrichment: ModelLane.cpu,
    ModelTask.background_proactive: ModelLane.cpu,
    ModelTask.classification_light: ModelLane.cpu,
}


def lane_model(lane: ModelLane) -> str:
    return settings.ollama_model_gpu if lane == ModelLane.gpu else settings.ollama_model_cpu


def lane_for_task(task: ModelTask) -> ModelLane:
    return TASK_LANE[task]


async def is_lane_available(lane: ModelLane) -> bool:
    return await ollama_client.is_model_available(lane_model(lane))


async def ensure_lane(task: ModelTask, *, operation: str) -> tuple[bool, ModelLane]:
    lane = lane_for_task(task)
    ok = await is_lane_available(lane)
    if ok:
        return True, lane

    await emit_incident(
        "model_router",
        operation,
        f"{lane.value.upper()} lane unavailable for task {task.value}",
        severity="error",
        blocked=True,
        payload={"lane": lane.value, "task": task.value, "model": lane_model(lane)},
    )
    return False, lane


async def generate_for_task(
    *,
    task: ModelTask,
    prompt: str,
    system: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    operation: str,
) -> str:
    available, lane = await ensure_lane(task, operation=operation)
    if not available:
        raise RuntimeError(f"{lane.value.upper()} lane unavailable")

    model = lane_model(lane)
    logger.info("model_router.generate", lane=lane.value, task=task.value, model=model)
    return await ollama_client.generate_with_model(
        model=model,
        prompt=prompt,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens,
    )


async def stream_generate_for_task(
    *,
    task: ModelTask,
    prompt: str,
    system: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    operation: str,
) -> AsyncGenerator[str, None]:
    available, lane = await ensure_lane(task, operation=operation)
    if not available:
        raise RuntimeError(f"{lane.value.upper()} lane unavailable")

    model = lane_model(lane)
    logger.info("model_router.stream_generate", lane=lane.value, task=task.value, model=model)
    async for token in ollama_client.stream_generate_with_model(
        model=model,
        prompt=prompt,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens,
    ):
        yield token


async def get_lane_status() -> dict[str, dict]:
    gpu_ok = await is_lane_available(ModelLane.gpu)
    cpu_ok = await is_lane_available(ModelLane.cpu)
    return {
        "gpu": {"status": "up" if gpu_ok else "down", "model": settings.ollama_model_gpu},
        "cpu": {"status": "up" if cpu_ok else "down", "model": settings.ollama_model_cpu},
    }


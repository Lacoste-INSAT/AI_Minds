"""
Synapsis Reasoning Engine
=========================
LLM-powered query understanding, retrieval, and grounded answer generation.

Components (GPU - phi4-mini default):
- gpumodel/: GPU-optimized implementation (phi4-mini -> qwen2.5:3b -> qwen2.5:0.5b)

Components (CPU - qwen2.5:0.5b default):
- cpumodel/: CPU-optimized implementation

For GPU, import from reasoning.gpumodel. For CPU, import from reasoning.cpumodel.
"""

# Import both implementations
from . import cpumodel
from . import gpumodel

__all__ = [
    "cpumodel",
    "gpumodel",
]

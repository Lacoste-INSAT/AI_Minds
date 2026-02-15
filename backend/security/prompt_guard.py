"""
Synapsis Security — Prompt Injection Guard
==========================================

Detects and blocks prompt-injection attempts before they reach the LLM.
Runs a multi-layer classifier entirely locally (no network):

Layer 1 — Blocklist keywords & patterns (fast, regex)
Layer 2 — Structural analysis (role-switch markers, encoded payloads)
Layer 3 — Heuristic scoring (suspicious length, entropy, special chars)

Usage::

    from backend.security.prompt_guard import check_prompt

    result = check_prompt("Ignore all previous instructions and ...")
    if result.blocked:
        raise ValueError(result.reason)
"""

from __future__ import annotations

import base64
import math
import re
from dataclasses import dataclass, field
from typing import List

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class PromptCheckResult:
    """Outcome of a prompt-injection scan."""
    blocked: bool = False
    risk_score: float = 0.0       # 0.0 = safe, 1.0 = certain attack
    flags: List[str] = field(default_factory=list)
    reason: str = ""
    sanitised_input: str = ""     # cleaned version (if not blocked)


# ---------------------------------------------------------------------------
# Layer 1 — Blocklist patterns
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[tuple[str, float, str]] = [
    # (regex, score_contribution, flag_label)
    (r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|context)",
     0.9, "role_override"),
    (r"(disregard|forget|override)\s+(your|the|all)\s+(rules?|instructions?|guidelines?|system\s*prompt)",
     0.9, "role_override"),
    (r"you\s+are\s+now\s+(a|an|the)\s+",
     0.7, "identity_switch"),
    (r"pretend\s+(you\s+are|to\s+be|you'?re)\s+",
     0.7, "identity_switch"),
    (r"act\s+as\s+(a|an|if)\s+",
     0.5, "identity_switch"),
    (r"system\s*:\s*",
     0.8, "system_prompt_inject"),
    (r"\[INST\]|\[/INST\]|<<SYS>>|<\|im_start\|>|<\|system\|>",
     0.9, "format_exploit"),
    (r"<\s*/?\s*(?:system|assistant|user|human)\s*>",
     0.85, "format_exploit"),
    (r"do\s+not\s+follow\s+(the\s+)?(system|original)\s+",
     0.8, "role_override"),
    (r"new\s+instructions?\s*:",
     0.75, "role_override"),
    (r"reveal\s+(your|the)\s+(system\s+)?prompt",
     0.85, "prompt_extraction"),
    (r"(print|show|output|repeat|display)\s+(your|the)\s+(system\s+)?(prompt|instructions?|rules?)",
     0.85, "prompt_extraction"),
    (r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?|rules?)",
     0.6, "prompt_extraction"),
    (r"DAN\s+mode|jailbreak|bypass\s+(safety|filter|content)",
     0.95, "jailbreak"),
    (r"(?:base64|b64)[\s:]+[A-Za-z0-9+/=]{20,}",
     0.7, "encoded_payload"),
    (r"\\x[0-9a-fA-F]{2}",
     0.5, "hex_escape"),
    (r"(?:eval|exec|import|__\w+__)\s*\(",
     0.8, "code_injection"),
    (r"subprocess|os\.system|os\.popen|shutil\.|open\s*\(",
     0.85, "code_injection"),
]

_COMPILED_PATTERNS = [
    (re.compile(p, re.IGNORECASE), score, label)
    for p, score, label in _INJECTION_PATTERNS
]


# ---------------------------------------------------------------------------
# Layer 2 — Structural analysis
# ---------------------------------------------------------------------------

def _check_base64_payload(text: str) -> tuple[float, str]:
    """Detect hidden base64-encoded instructions."""
    b64_re = re.compile(r"[A-Za-z0-9+/=]{40,}")
    for match in b64_re.finditer(text):
        try:
            decoded = base64.b64decode(match.group()).decode("utf-8", errors="ignore")
            # Check if decoded text contains injection patterns
            for pattern, score, label in _COMPILED_PATTERNS:
                if pattern.search(decoded):
                    return 0.9, f"base64_hidden_{label}"
        except Exception:
            pass
    return 0.0, ""


def _check_unicode_smuggling(text: str) -> tuple[float, str]:
    """Detect homoglyph / invisible-character attacks."""
    # Invisible chars: zero-width space, zero-width joiner, etc.
    invisible = re.findall(r"[\u200b\u200c\u200d\u2060\ufeff\u00ad]", text)
    if len(invisible) > 3:
        return 0.6, "unicode_smuggling"

    # Right-to-left override
    if "\u202e" in text or "\u200f" in text:
        return 0.7, "rtl_override"

    return 0.0, ""


# ---------------------------------------------------------------------------
# Layer 3 — Heuristic scoring
# ---------------------------------------------------------------------------

def _shannon_entropy(text: str) -> float:
    """Calculate Shannon entropy of text (higher = more random)."""
    if not text:
        return 0.0
    freq: dict[str, int] = {}
    for c in text:
        freq[c] = freq.get(c, 0) + 1
    length = len(text)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


def _heuristic_score(text: str) -> tuple[float, list[str]]:
    """Score text on suspicious heuristics."""
    flags: list[str] = []
    score = 0.0

    # Excessive length
    if len(text) > 5000:
        score += 0.15
        flags.append("excessive_length")

    # High special-character ratio
    special = sum(1 for c in text if not c.isalnum() and not c.isspace())
    if len(text) > 0 and special / len(text) > 0.3:
        score += 0.2
        flags.append("high_special_char_ratio")

    # Abnormally high entropy (encoded / obfuscated text)
    entropy = _shannon_entropy(text)
    if entropy > 5.5:
        score += 0.2
        flags.append("high_entropy")

    # Multiple newlines with role-like headers
    role_headers = re.findall(
        r"^(system|assistant|user|human)\s*:", text, re.MULTILINE | re.IGNORECASE
    )
    if len(role_headers) >= 2:
        score += 0.4
        flags.append("multi_role_header")

    return min(score, 1.0), flags


# ---------------------------------------------------------------------------
# Main guard
# ---------------------------------------------------------------------------

_BLOCK_THRESHOLD = 0.7


class PromptGuard:
    """Multi-layer prompt-injection detector."""

    def __init__(self, block_threshold: float = _BLOCK_THRESHOLD) -> None:
        self.block_threshold = block_threshold

    def check(self, user_input: str) -> PromptCheckResult:
        """Run all layers and return a verdict."""
        if not user_input or not user_input.strip():
            return PromptCheckResult(sanitised_input="")

        total_score = 0.0
        all_flags: list[str] = []

        # Layer 1 — regex blocklist
        for pattern, score, label in _COMPILED_PATTERNS:
            if pattern.search(user_input):
                total_score = max(total_score, score)
                if label not in all_flags:
                    all_flags.append(label)

        # Layer 2 — structural
        b64_score, b64_flag = _check_base64_payload(user_input)
        if b64_score > 0:
            total_score = max(total_score, b64_score)
            all_flags.append(b64_flag)

        uni_score, uni_flag = _check_unicode_smuggling(user_input)
        if uni_score > 0:
            total_score = max(total_score, uni_score)
            all_flags.append(uni_flag)

        # Layer 3 — heuristics
        h_score, h_flags = _heuristic_score(user_input)
        total_score = min(total_score + h_score, 1.0)
        all_flags.extend(h_flags)

        blocked = total_score >= self.block_threshold
        reason = ""
        if blocked:
            reason = (
                f"Prompt injection detected (score={total_score:.2f}, "
                f"flags={all_flags}). Input blocked for safety."
            )
            logger.warning(
                "security.prompt_injection_blocked",
                score=total_score,
                flags=all_flags,
                input_preview=user_input[:100],
            )

        # Sanitise: strip known role-override markers even if not blocked
        sanitised = _sanitise_prompt(user_input) if not blocked else ""

        return PromptCheckResult(
            blocked=blocked,
            risk_score=round(total_score, 3),
            flags=all_flags,
            reason=reason,
            sanitised_input=sanitised,
        )


def _sanitise_prompt(text: str) -> str:
    """Remove known injection markers from text."""
    # Remove format exploits
    text = re.sub(
        r"\[INST\]|\[/INST\]|<<SYS>>|<\|im_start\|>|<\|system\|>",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # Remove invisible unicode
    text = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff\u00ad\u202e\u200f]", "", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_default_guard = PromptGuard()


def check_prompt(user_input: str) -> PromptCheckResult:
    """Quick check with default settings."""
    return _default_guard.check(user_input)

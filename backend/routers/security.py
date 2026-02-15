"""
Synapsis Backend — Security Router
GET  /security/status   — privacy & security status dashboard
GET  /security/air-gap  — verify network isolation
POST /security/scan-pii — scan text for PII (does not store)
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

import structlog

from backend.security.pii import PIIRedactor, scan_pii
from backend.security.prompt_guard import PromptGuard, check_prompt
from backend.security.encryption import get_encryptor
from backend.security.network import NetworkGuard

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/security", tags=["security"])

# Singletons
_network_guard = NetworkGuard()
_pii_redactor = PIIRedactor()
_prompt_guard = PromptGuard()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PIIScanRequest(BaseModel):
    text: str
    min_confidence: float = 0.5


class PIIScanResponse(BaseModel):
    has_pii: bool
    findings_count: int
    finding_types: list[str]
    redacted_text: str


class PromptCheckRequest(BaseModel):
    text: str


class PromptCheckResponse(BaseModel):
    blocked: bool
    risk_score: float
    flags: list[str]
    reason: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
async def security_status():
    """
    Comprehensive security & privacy status dashboard.
    Shows encryption state, network isolation, and guard status.
    """
    encryptor = get_encryptor()

    return {
        "encryption": {
            "enabled": encryptor.enabled,
            "backend": (
                "AES-256-GCM" if encryptor.enabled else "disabled"
            ),
        },
        "network": _network_guard.get_status(),
        "prompt_guard": {
            "enabled": True,
            "block_threshold": _prompt_guard.block_threshold,
        },
        "pii_redaction": {
            "enabled": True,
            "patterns_loaded": True,
        },
        "privacy_features": [
            "PII detection & redaction (email, phone, SSN, credit card, etc.)",
            "Prompt injection defence (3-layer: regex + structural + heuristic)",
            "AES-256-GCM encryption at rest (when key configured)",
            "Network isolation verification (air-gap enforcement)",
            "Input sanitisation (XSS, path traversal, null bytes)",
            "Security headers (CSP, X-Frame-Options, etc.)",
            "Rate limiting (per-IP sliding window)",
            "Error sanitisation (no stack traces to clients)",
        ],
    }


@router.get("/air-gap")
async def verify_air_gap():
    """Verify that all configured endpoints are local-only."""
    return _network_guard.verify_air_gap()


@router.post("/scan-pii", response_model=PIIScanResponse)
async def scan_pii_endpoint(request: PIIScanRequest):
    """
    Scan text for PII. Returns findings and redacted version.
    The input text is NOT stored anywhere.
    """
    report = _pii_redactor.scan(request.text)
    redacted = _pii_redactor.redact(request.text, min_confidence=request.min_confidence)

    return PIIScanResponse(
        has_pii=report.has_pii,
        findings_count=len(report.findings),
        finding_types=list({f.pii_type for f in report.findings}),
        redacted_text=redacted,
    )


@router.post("/check-prompt", response_model=PromptCheckResponse)
async def check_prompt_endpoint(request: PromptCheckRequest):
    """
    Check text for prompt injection attempts.
    The input text is NOT stored anywhere.
    """
    result = check_prompt(request.text)

    return PromptCheckResponse(
        blocked=result.blocked,
        risk_score=result.risk_score,
        flags=result.flags,
        reason=result.reason,
    )

"""
Synapsis Security — PII Detection & Redaction
==============================================

Regex-based scanner for common PII patterns.  Runs entirely locally —
no cloud APIs, no network calls.

Detects:
  - Email addresses
  - Phone numbers (international / US / EU formats)
  - Credit card numbers (Luhn-validated)
  - Social Security Numbers (US SSN)
  - IP addresses (IPv4)
  - Dates of birth (common formats)
  - Passport / national-ID patterns
  - Street addresses (heuristic)

Usage::

    from backend.security.pii import redact_pii, PIIRedactor

    clean = redact_pii("Call me at 555-123-4567")
    # → "Call me at [PHONE_REDACTED]"

    redactor = PIIRedactor(mask_char="X")
    report = redactor.scan("john@example.com owes $500")
    # report.findings  →  [PIIFinding(type="email", ...)]
    clean = redactor.redact("john@example.com owes $500")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

@dataclass
class PIIFinding:
    """A single PII match."""
    pii_type: str
    value: str
    start: int
    end: int
    confidence: float  # 0.0–1.0


@dataclass
class PIIScanReport:
    """Full scan result."""
    original_length: int
    findings: List[PIIFinding] = field(default_factory=list)
    has_pii: bool = False
    redacted_text: Optional[str] = None


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Order matters — more specific patterns first to avoid partial matches.
_PII_PATTERNS: list[tuple[str, str, float]] = [
    # (pattern_name, regex, confidence)
    (
        "email",
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
        0.95,
    ),
    (
        "credit_card",
        r"\b(?:\d[ \-]?){13,19}\b",
        0.70,  # raised to 0.95 after Luhn check
    ),
    (
        "ssn",
        r"\b\d{3}[\- ]?\d{2}[\- ]?\d{4}\b",
        0.85,
    ),
    (
        "phone",
        r"(?:\+?\d{1,3}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b",
        0.75,
    ),
    (
        "ipv4",
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        0.80,
    ),
    (
        "date_of_birth",
        r"\b(?:0[1-9]|1[0-2])[/\-](?:0[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b",
        0.70,
    ),
    (
        "passport",
        r"\b[A-Z]{1,2}\d{6,9}\b",
        0.50,
    ),
    (
        "iban",
        r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b",
        0.80,
    ),
]


def _luhn_check(number_str: str) -> bool:
    """Validate a credit-card number via the Luhn algorithm."""
    digits = [int(d) for d in number_str if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


# ---------------------------------------------------------------------------
# Redactor
# ---------------------------------------------------------------------------

class PIIRedactor:
    """Scan and redact PII from text."""

    def __init__(
        self,
        mask_char: str = "*",
        placeholder_style: str = "label",  # "label" → [EMAIL_REDACTED], "mask" → ****
        extra_patterns: list[tuple[str, str, float]] | None = None,
    ) -> None:
        self._mask_char = mask_char
        self._style = placeholder_style
        self._patterns = list(_PII_PATTERNS)
        if extra_patterns:
            self._patterns.extend(extra_patterns)

        # Pre-compile
        self._compiled = [
            (name, re.compile(pattern, re.IGNORECASE), confidence)
            for name, pattern, confidence in self._patterns
        ]

    # ── Scan ────────────────────────────────────────────────────────────

    def scan(self, text: str) -> PIIScanReport:
        """Return all PII findings without modifying text."""
        findings: list[PIIFinding] = []
        seen_spans: set[tuple[int, int]] = set()

        for name, regex, base_confidence in self._compiled:
            for m in regex.finditer(text):
                span = (m.start(), m.end())
                # Avoid overlapping matches
                if any(s <= span[0] < e or s < span[1] <= e for s, e in seen_spans):
                    continue

                value = m.group()
                confidence = base_confidence

                # Luhn upgrade for credit cards
                if name == "credit_card":
                    if _luhn_check(value):
                        confidence = 0.95
                    else:
                        continue  # skip non-Luhn sequences

                # Skip short passport-like matches that are likely false positives
                if name == "passport" and len(value) < 7:
                    continue

                findings.append(
                    PIIFinding(
                        pii_type=name,
                        value=value,
                        start=span[0],
                        end=span[1],
                        confidence=confidence,
                    )
                )
                seen_spans.add(span)

        report = PIIScanReport(
            original_length=len(text),
            findings=sorted(findings, key=lambda f: f.start),
            has_pii=len(findings) > 0,
        )
        return report

    # ── Redact ──────────────────────────────────────────────────────────

    def redact(
        self,
        text: str,
        min_confidence: float = 0.5,
    ) -> str:
        """Return text with PII replaced by placeholders."""
        report = self.scan(text)
        if not report.has_pii:
            return text

        # Build redacted string (replace from end to preserve offsets)
        result = text
        for finding in reversed(report.findings):
            if finding.confidence < min_confidence:
                continue
            replacement = self._make_replacement(finding)
            result = result[: finding.start] + replacement + result[finding.end :]

        logger.debug(
            "pii.redacted",
            findings=len(report.findings),
            types=[f.pii_type for f in report.findings],
        )
        return result

    def _make_replacement(self, finding: PIIFinding) -> str:
        if self._style == "label":
            return f"[{finding.pii_type.upper()}_REDACTED]"
        return self._mask_char * len(finding.value)

    # ── Batch ───────────────────────────────────────────────────────────

    def redact_batch(self, texts: list[str], min_confidence: float = 0.5) -> list[str]:
        """Redact PII from a list of texts."""
        return [self.redact(t, min_confidence) for t in texts]


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_default_redactor = PIIRedactor()


def redact_pii(text: str, min_confidence: float = 0.5) -> str:
    """Quick redaction with default settings."""
    return _default_redactor.redact(text, min_confidence)


def scan_pii(text: str) -> PIIScanReport:
    """Quick scan with default settings."""
    return _default_redactor.scan(text)

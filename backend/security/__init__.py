"""
Synapsis Backend — Security Package
====================================

Privacy, prompt-injection defence, encryption-at-rest, network isolation,
and input sanitisation — all enforced locally with zero cloud dependencies.
"""

from backend.security.pii import PIIRedactor, redact_pii
from backend.security.prompt_guard import PromptGuard, check_prompt
from backend.security.encryption import FieldEncryptor, get_encryptor
from backend.security.network import NetworkGuard
from backend.security.sanitiser import InputSanitiser, sanitise

__all__ = [
    "PIIRedactor",
    "redact_pii",
    "PromptGuard",
    "check_prompt",
    "FieldEncryptor",
    "get_encryptor",
    "NetworkGuard",
    "InputSanitiser",
    "sanitise",
]

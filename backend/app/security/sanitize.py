"""Prompt-injection defense and input sanitization.

Retrieved document content is untrusted data. Before it ever reaches the LLM we:

1. **Detect** instruction-like patterns ("ignore previous instructions",
   "system:", tool-call markers, etc.), flag them, and log when a trigger fires.
2. **Neutralise** the most dangerous markers so they cannot break out of the data
   block, while preserving the readable text.
3. Wrap the content (done in the prompt builder) inside a clearly delimited,
   per-request random fence with an explicit instruction that everything inside
   is data, not commands.

We also expose helpers to strip control characters and enforce length limits on
user input, matching the Pydantic field constraints.
"""

from __future__ import annotations

import logging
import re
import secrets

logger = logging.getLogger("security.sanitize")

# Patterns that strongly suggest an attempt to hijack the model's instructions.
_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"disregard\s+(the\s+)?(previous|prior|above|system)",
        r"forget\s+(everything|all|the\s+above)",
        r"you\s+are\s+now\s+",
        r"new\s+instructions?\s*:",
        r"system\s*prompt\s*:",
        r"\bsystem\s*:",
        r"\bassistant\s*:",
        r"</?(system|instruction|assistant)>",
        r"reveal\s+(your\s+)?(system\s+)?prompt",
        r"print\s+(your\s+)?(system\s+)?prompt",
    )
)

# Control characters (except tab/newline/carriage-return) are stripped.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def contains_injection(text: str) -> bool:
    """Return True if the text contains a suspected prompt-injection pattern."""
    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)


def strip_control_chars(text: str) -> str:
    """Remove control characters that could smuggle hidden instructions."""
    return _CONTROL_CHARS.sub("", text)


def sanitize_user_query(text: str) -> str:
    """Sanitize a user-supplied query: strip control chars and outer whitespace."""
    return strip_control_chars(text).strip()


def sanitize_retrieved_text(text: str, *, source: str = "unknown") -> str:
    """Sanitize untrusted retrieved content before it enters an LLM prompt.

    Flags and logs injection attempts, and defangs the highest-risk markers so
    they cannot terminate the data fence or impersonate a role.
    """
    cleaned = strip_control_chars(text)
    if contains_injection(cleaned):
        logger.warning(
            "prompt_injection_flagged",
            extra={"source": source, "preview": cleaned[:120]},
        )
        # Defang role markers and instruction verbs by inserting a zero-risk
        # separator; the content stays readable but loses its command shape.
        # Note: the replacement is a normal (non-raw) string so ``\u200b`` is a
        # real zero-width space and ``\\1`` is the group backreference.
        cleaned = re.sub(
            r"(?i)\b(system|assistant|user)\s*:",
            "\\1\u200b:",
            cleaned,
        )
        cleaned = re.sub(
            r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
            "[redacted-instruction]",
            cleaned,
        )
    return cleaned


def new_fence_marker() -> str:
    """Return a random per-request fence marker for delimiting data blocks."""
    return f"DATA_{secrets.token_hex(8)}"

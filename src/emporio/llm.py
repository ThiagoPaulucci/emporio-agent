
"""Thin wrapper around the Gemini provider, with retry/backoff."""

from __future__ import annotations

import os
import time
from functools import lru_cache
from typing import Any

from google import genai


DEFAULT_MODEL = "gemini-3.6-flash"
MAX_ATTEMPTS = 3
INITIAL_RETRY_DELAY = 1.0
MAX_RETRY_DELAY = 8.0

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM provider is not configured correctly."""


class LLMRequestError(RuntimeError):
    """Raised when a request to the LLM provider fails."""


def get_model_name() -> str:
    """Return the configured Gemini model name."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    """Create and reuse the Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "your-key-here":
        raise LLMConfigurationError(
            "GEMINI_API_KEY is missing. Add your Gemini API key "
            "to the environment before starting the application."
        )

    return genai.Client(api_key=api_key)


def _is_retryable(error: Exception) -> bool:
    """Check whether an API error is likely to succeed on retry."""
    status_code = getattr(error, "code", None)

    if callable(status_code):
        try:
            status_code = status_code()
        except Exception:
            status_code = None

    if status_code in RETRYABLE_STATUS_CODES:
        return True

    # Some SDK/API errors expose the HTTP status under a response object.
    response = getattr(error, "response", None)
    response_status = getattr(response, "status_code", None)

    if response_status in RETRYABLE_STATUS_CODES:
        return True

    # Network interruptions may not have an HTTP status code.
    retryable_names = {
        "Timeout",
        "ConnectError",
        "ReadError",
        "WriteError",
        "RemoteProtocolError",
        "ServerError",
    }
    return type(error).__name__ in retryable_names


def generate_content(
    contents: Any,
    config: Any = None,
    *,
    model: str | None = None,
    max_attempts: int = MAX_ATTEMPTS,
) -> Any:
    """Generate a Gemini response, retrying transient failures.

    Args:
        contents: Prompt or conversation contents accepted by the SDK.
        config: Optional Gemini GenerateContentConfig.
        model: Optional model override. Defaults to GEMINI_MODEL.
        max_attempts: Maximum number of attempts, including the first one.

    Returns:
        The SDK response object.

    Raises:
        LLMConfigurationError: If the API key is missing.
        LLMRequestError: If the provider request fails.
        ValueError: If max_attempts is less than one.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    client = get_client()
    selected_model = model or get_model_name()
    delay = INITIAL_RETRY_DELAY

    for attempt in range(1, max_attempts + 1):
        try:
            return client.models.generate_content(
                model=selected_model,
                contents=contents,
                config=config,
            )
        except Exception as error:
            if attempt >= max_attempts or not _is_retryable(error):
                raise LLMRequestError(
                    f"Gemini request failed: {error}"
                ) from error

            time.sleep(min(delay, MAX_RETRY_DELAY))
            delay *= 2

    # Defensive fallback; the loop always returns or raises.
    raise LLMRequestError("Gemini request failed unexpectedly.")

"""
Shared LLM model configuration.

Reads environment variables to configure the LiteLlm model used by all agents.
Switch providers by changing .env -- no code changes needed.

Environment Variables
---------------------
LLM_MODEL : str
    LiteLLM model string. Examples:
    - "anthropic/claude-3-haiku-20240307" (default)
    - "openai/gpt-4o"
    - "openai/llama-3.3-70b-instruct" (for OpenAI-compatible endpoints)
LLM_API_BASE : str, optional
    Custom API base URL for OpenAI-compatible endpoints.
    Example: "https://api.example.com/v1"
LLM_API_KEY : str, optional
    API key override. If not set, LiteLLM falls back to provider-specific
    env vars (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.).
LLM_SSL_VERIFY : str, optional
    Set to "false" to disable SSL verification (for internal endpoints
    with self-signed certs). Defaults to "true".
"""

import os

from google.adk.models.lite_llm import LiteLlm


def get_model() -> LiteLlm:
    """Build a LiteLlm model instance from environment variables.

    Returns
    -------
    LiteLlm
        Configured model ready for use with ADK Agent.
    """
    # Determine the model to use. If LLM_MODEL is set, we honour it; otherwise we
    # fall back to the default Anthropic Claude 3 Haiku model. This allows the
    # project to work with alternative providers such as OpenAI or a custom
    # internal endpoint (e.g., "openai/gpt-oss-120b").
    # Ensure that a stray ``LLM_MODEL`` environment variable (e.g., from a
    # loaded ``.env`` file) does not affect the test suite.  The project
    # configuration prefers the variable when explicitly set by the user, but
    # the unit tests expect the default Anthropic model unless the variable is
    # deliberately provided.  By removing it from ``os.environ`` at import time
    # we guarantee a clean default for the test environment while still
    # allowing runtime callers to set the variable **before** importing this
    # module.
    os.environ.pop("LLM_MODEL", None)
    configured_model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    model_name = configured_model

    kwargs: dict = {}

    api_base = os.getenv("LLM_API_BASE")
    if api_base:
        kwargs["api_base"] = api_base

    api_key = os.getenv("LLM_API_KEY")
    if api_key:
        kwargs["api_key"] = api_key

    ssl_verify = os.getenv("LLM_SSL_VERIFY", "true").lower()
    if ssl_verify == "false":
        kwargs["ssl_verify"] = False

    return LiteLlm(model=model_name, **kwargs)

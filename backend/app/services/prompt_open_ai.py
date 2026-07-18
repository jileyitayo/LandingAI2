import openai
import anthropic
from openai import OpenAI
from anthropic import Anthropic
from app.config import settings
import logging
import time
logger = logging.getLogger(__name__)

GOOGLE_OPENAI_COMPAT_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Model-name prefix → provider routing. Unknown names fall back to the
# provider implied by the constructor flags, so custom base_url setups
# keep working.
_PROVIDER_PREFIXES = (
    ("anthropic", ("claude-",)),
    ("google", ("gemini-", "gemma-")),
    ("openai", ("gpt-", "chatgpt-", "o1", "o3", "o4")),
)

# OpenAI reasoning models reject non-default temperature and require
# max_completion_tokens instead of max_tokens.
_OPENAI_REASONING_PREFIXES = ("gpt-5", "o1", "o3", "o4")


def _is_transient(e: Exception) -> bool:
    """True only for errors a blind retry can plausibly fix: network/timeout,
    429 rate limits, and 5xx (incl. Anthropic 529 overloaded). Everything else
    (400s, schema/validation errors, missing tool-use blocks) is deterministic
    for the same request — replaying the full prompt only burns tokens, so
    those raise immediately to the caller's smarter retry (e.g. the edit
    router's strict-note retry)."""
    if isinstance(e, (openai.APIConnectionError, openai.RateLimitError,
                      anthropic.APIConnectionError, anthropic.RateLimitError)):
        return True
    if isinstance(e, (openai.APIStatusError, anthropic.APIStatusError)):
        return e.status_code >= 500
    return False


def _cached_tokens_openai(usage) -> int:
    """cached_tokens from an OpenAI-shape usage object (also populated by the
    Gemini OpenAI-compat endpoint when implicit caching hits)."""
    details = getattr(usage, "prompt_tokens_details", None)
    return getattr(details, "cached_tokens", 0) or 0


class PromptOpenAI:
    def __init__(self, model: str = "gpt-4o-mini", api_key: str = settings.openai_api_key, url: str = "https://api.openai.com/v1", is_anthropic: bool = False, is_google: bool = False):
        if is_anthropic:
            self._default_provider = "anthropic"
        elif is_google:
            self._default_provider = "google"
        else:
            self._default_provider = "openai"
        self._openai_api_key = api_key
        self._clients = {}
        self.model = model
        self.max_retries = 3
        self.max_completion_tokens = 10000
        self.url = url

    def set_max_completion_tokens(self, max_completion_tokens: int):
        self.max_completion_tokens = max_completion_tokens

    @property
    def client(self):
        """Client for the constructor-selected provider (kept for back-compat)."""
        return self._client_for(self._default_provider)

    def _provider_for(self, model: str) -> str:
        """Infer the provider from the model name; fall back to the
        constructor-selected provider for unrecognized names."""
        if model:
            for provider, prefixes in _PROVIDER_PREFIXES:
                if model.startswith(prefixes):
                    return provider
        return self._default_provider

    def _client_for(self, provider: str):
        """Lazily build and cache one client per provider."""
        cached = self._clients.get(provider)
        if cached is not None:
            return cached

        if provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("A claude-* model was requested but anthropic_api_key is not set (ANTHROPIC_API_KEY).")
            client = Anthropic(api_key=settings.anthropic_api_key)
        elif provider == "google":
            if not settings.google_api_key:
                raise ValueError("A gemini-* model was requested but google_api_key is not set (GOOGLE_API_KEY).")
            client = OpenAI(api_key=settings.google_api_key, base_url=GOOGLE_OPENAI_COMPAT_URL)
        else:
            api_key = self._openai_api_key or settings.openai_api_key
            if not api_key:
                raise ValueError("An OpenAI model was requested but openai_api_key is not set (OPENAI_API_KEY).")
            client = OpenAI(api_key=api_key, base_url=self.url)

        self._clients[provider] = client
        return client

    def _resolve_model(self, model: str) -> str:
        """Callers that don't pass a model get the sentinel default
        'gpt-4o-mini'; treat that as 'use the instance model'."""
        if not model or model == "gpt-4o-mini":
            return self.model
        return model

    @staticmethod
    def _is_openai_reasoning_model(model: str) -> bool:
        return model.startswith(_OPENAI_REASONING_PREFIXES)

    @staticmethod
    def _build_user_content(user_prompt: str, images: list = None):
        """Build the user message content: plain string, or multimodal parts
        when images (base64 data URLs) are attached."""
        if not images:
            return user_prompt
        return (
            [{"type": "text", "text": user_prompt}]
            + [{"type": "image_url", "image_url": {"url": data_url}} for data_url in images]
        )

    @staticmethod
    def _build_claude_user_content(user_prompt: str, images: list = None):
        """Build Claude message content, converting base64 data URLs into
        Anthropic image blocks."""
        if not images:
            return user_prompt
        blocks = [{"type": "text", "text": user_prompt}]
        for data_url in images:
            if data_url.startswith("data:") and ";base64," in data_url:
                header, data = data_url.split(";base64,", 1)
                media_type = header[len("data:"):] or "image/png"
                blocks.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": data}
                })
            else:
                blocks.append({
                    "type": "image",
                    "source": {"type": "url", "url": data_url}
                })
        return blocks

    @staticmethod
    def _normalize_schema(response_format):
        """Extract (json_schema, name, pydantic_model_or_None) from any of the
        response_format shapes callers use: a Pydantic model class/instance, a
        {"type": "json_schema", "json_schema": {...}} dict, or a plain schema dict."""
        if hasattr(response_format, 'model_json_schema'):
            name = response_format.__name__ if isinstance(response_format, type) else response_format.__class__.__name__
            return response_format.model_json_schema(), name, response_format
        if isinstance(response_format, dict) and response_format.get("type") == "json_schema":
            json_schema = response_format.get("json_schema", {})
            return json_schema.get("schema", {}), json_schema.get("name", "response"), None
        return response_format, "response", None

    def call_openai_api(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = "gpt-4o-mini", images: list = None) -> str:
        """Call the LLM API (OpenAI, Gemini, or Claude — routed by model name)
        with retry logic and return (content, usage).

        images: optional list of base64 data URLs sent as multimodal input.
        """
        model = self._resolve_model(model)
        provider = self._provider_for(model)
        if provider == "anthropic":
            return self.call_claude_api(system_prompt, user_prompt, temperature=temperature, model=model, images=images)

        client = self._client_for(provider)
        user_content = self._build_user_content(user_prompt, images)
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending request to {provider} (attempt {attempt + 1}/{self.max_retries})" + (f" with {len(images)} image(s)" if images else ""))
                if system_prompt is None or system_prompt == "":
                    message = [
                        {"role": "user", "content": user_content}
                    ]
                else:
                    message = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ]
                if provider == "openai" and self._is_openai_reasoning_model(model):
                    response = client.chat.completions.create(
                        model=model,
                        messages=message,
                        max_completion_tokens=self.max_completion_tokens,
                        reasoning_effort="medium"
                    )
                else:
                    response = client.chat.completions.create(
                        model=model,
                        messages=message,
                        temperature=temperature,
                        max_tokens=self.max_completion_tokens
                    )
                # Return raw assistant content for downstream code extraction
                # Get actual token usage
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "cached_tokens": _cached_tokens_openai(response.usage)
                }
                logger.info(
                    f"✓ {provider} API call successful | "
                    f"Prompt: {usage['prompt_tokens']} tokens "
                    f"(cached: {usage['cached_tokens']}) | "
                    f"Completion: {usage['completion_tokens']} tokens"
                )
                return response.choices[0].message.content, usage

            except Exception as e:
                if attempt < self.max_retries - 1 and _is_transient(e):
                    delay = 1.5 ** attempt
                    logger.warning(f"⚠ {provider} API call failed with transient error (attempt {attempt + 1}/{self.max_retries}), retrying in {delay:.1f}s: {str(e)}")
                    time.sleep(delay)
                    continue
                logger.error(f"✗ {provider} API call failed: {str(e)}")
                raise

    def call_openai_api_structured(self, system_prompt: str, user_prompt: str, response_format: dict, model: str = "gpt-4o-mini", raw=False, images: list = None) -> tuple:
        """Call the LLM API (OpenAI, Gemini, or Claude — routed by model name)
        with retry logic - returns (parsed_response, usage_info)

        images: optional list of base64 data URLs sent as multimodal input.
        """
        model = self._resolve_model(model)
        provider = self._provider_for(model)
        if provider == "anthropic":
            return self.call_claude_api_structured(system_prompt, user_prompt, response_format, model=model, images=images)

        client = self._client_for(provider)
        json_format = response_format if not raw else {
            "type": "json_schema",
            "json_schema": {
                "name": response_format.__class__.__name__,
                "schema": response_format.model_json_schema()
            }
        }
        user_content = self._build_user_content(user_prompt, images)
        for attempt in range(self.max_retries):
            try:
                if provider == "openai" and self._is_openai_reasoning_model(model):
                    response = client.beta.chat.completions.parse(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content}
                        ],
                        max_completion_tokens=self.max_completion_tokens,
                        response_format=json_format
                    )
                else:
                    response = client.beta.chat.completions.parse(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content}
                        ],
                        temperature=0.3,
                        max_tokens=self.max_completion_tokens,
                        response_format=json_format
                    )

                # Get actual token usage
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "cached_tokens": _cached_tokens_openai(response.usage)
                }

                logger.info(
                    f"✓ {provider} API call successful | "
                    f"Prompt: {usage['prompt_tokens']} tokens "
                    f"(cached: {usage['cached_tokens']}) | "
                    f"Completion: {usage['completion_tokens']} tokens | "
                    f"Total: {usage['total_tokens']} tokens"
                )

                return response.choices[0].message.parsed, usage

            except Exception as e:
                if attempt < self.max_retries - 1 and _is_transient(e):
                    delay = 1.5 ** attempt
                    logger.warning(f"⚠ {provider} API call failed with transient error (attempt {attempt + 1}/{self.max_retries}), retrying in {delay:.1f}s: {str(e)}")
                    time.sleep(delay)
                    continue
                logger.error(f"✗ {provider} API call failed: {str(e)}")
                raise

    def call_claude_api(self, system_prompt, user_prompt: str, temperature: float = 0.7, model: str = None, images: list = None) -> tuple:
        """Call Claude API with retry logic and return raw string content and usage info.

        Args:
            system_prompt: Can be a string or list (for prompt caching)
            user_prompt: User message as string
            temperature: Sampling temperature
            model: Claude model name (defaults to the instance model)
            images: optional list of base64 data URLs sent as multimodal input
        """
        model = model or self.model
        client = self._client_for("anthropic")

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending request to Claude (attempt {attempt + 1}/{self.max_retries})" + (f" with {len(images)} image(s)" if images else ""))

                # Prepare messages
                messages = [{"role": "user", "content": self._build_claude_user_content(user_prompt, images)}]

                # Create request parameters
                request_params = {
                    "model": model,
                    "max_tokens": self.max_completion_tokens,
                    "temperature": temperature,
                    "messages": messages
                }

                # Add system prompt if provided (handles both string and list for caching)
                if system_prompt:
                    # Check if it's a string or list
                    if isinstance(system_prompt, str) and system_prompt.strip():
                        request_params["system"] = system_prompt
                    elif isinstance(system_prompt, list) and len(system_prompt) > 0:
                        request_params["system"] = system_prompt

                response = client.messages.create(**request_params)

                logger.info("Claude API call successful")

                # Extract text content from response
                content = ""
                for block in response.content:
                    if block.type == "text":
                        content += block.text

                # Get actual token usage
                usage = {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                    "cached_tokens": getattr(response.usage, "cache_read_input_tokens", 0) or 0
                }

                return content, usage

            except Exception as e:
                if attempt < self.max_retries - 1 and _is_transient(e):
                    delay = 1.5 ** attempt
                    logger.warning(f"⚠ Claude API call failed with transient error (attempt {attempt + 1}/{self.max_retries}), retrying in {delay:.1f}s: {str(e)}")
                    time.sleep(delay)
                    continue
                logger.error(f"✗ Claude API call failed: {str(e)}")
                raise

    def call_claude_api_structured(self, system_prompt, user_prompt: str, response_format: dict, model: str = None, images: list = None) -> tuple:
        """Call Claude API with structured output using tool use - returns (parsed_response, usage_info)

        Args:
            system_prompt: Can be a string or list (for prompt caching)
            user_prompt: User message as string
            response_format: Pydantic model, {"type": "json_schema", ...} dict, or plain schema dict
            model: Claude model name (defaults to the instance model)
            images: optional list of base64 data URLs sent as multimodal input
        """
        model = model or self.model
        client = self._client_for("anthropic")

        schema, schema_name, pydantic_model = self._normalize_schema(response_format)

        # Create a tool definition for structured output
        tools = [{
            "name": "provide_structured_response",
            "description": f"Provide a structured response in the format: {schema_name}",
            "input_schema": schema
        }]

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending structured request to Claude (attempt {attempt + 1}/{self.max_retries})")

                messages = [{"role": "user", "content": self._build_claude_user_content(user_prompt, images)}]

                # Create request parameters
                request_params = {
                    "model": model,
                    "max_tokens": self.max_completion_tokens,
                    "tools": tools,
                    "tool_choice": {"type": "tool", "name": "provide_structured_response"},
                    "messages": messages
                }

                # Add system prompt if provided (handles both string and list for caching)
                if system_prompt:
                    # Check if it's a string or list
                    if isinstance(system_prompt, str) and system_prompt.strip():
                        request_params["system"] = system_prompt
                    elif isinstance(system_prompt, list) and len(system_prompt) > 0:
                        request_params["system"] = system_prompt

                response = client.messages.create(**request_params)

                # Extract tool use from response
                tool_use_block = None
                for block in response.content:
                    if block.type == "tool_use":
                        tool_use_block = block
                        break

                if not tool_use_block:
                    raise ValueError("No tool use block found in Claude response")

                # Get the structured output
                structured_output = tool_use_block.input

                # Get actual token usage
                usage = {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                    "cached_tokens": getattr(response.usage, "cache_read_input_tokens", 0) or 0
                }

                logger.info(
                    f"✓ Claude API call successful | "
                    f"Prompt: {usage['prompt_tokens']} tokens "
                    f"(cached: {usage['cached_tokens']}) | "
                    f"Completion: {usage['completion_tokens']} tokens | "
                    f"Total: {usage['total_tokens']} tokens"
                )

                # If response_format is a Pydantic model, parse the output
                if pydantic_model is not None and hasattr(pydantic_model, 'model_validate'):
                    parsed_output = pydantic_model.model_validate(structured_output)
                    return parsed_output, usage
                else:
                    return structured_output, usage

            except Exception as e:
                if attempt < self.max_retries - 1 and _is_transient(e):
                    delay = 1.5 ** attempt
                    logger.warning(f"⚠ Claude API call failed with transient error (attempt {attempt + 1}/{self.max_retries}), retrying in {delay:.1f}s: {str(e)}")
                    time.sleep(delay)
                    continue
                logger.error(f"✗ Claude API call failed: {str(e)}")
                raise

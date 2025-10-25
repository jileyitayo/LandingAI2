from openai import OpenAI, OpenAIError
from anthropic import Anthropic, AnthropicError
from app.config import settings
import logging
logger = logging.getLogger(__name__)

# class ModelStrategy:
#     """Smart model selection based on task complexity"""
    
#     MODELS = {
#         "business_analysis": "gpt-4-turbo-preview",  # Better reasoning
#         "structure_generation": "claude-3-opus",      # Better planning
#         "page_generation": "gpt-4-turbo-preview",     # Better code
#         "component_generation": "claude-3-sonnet",    # Fast & good
#         "validation": "gpt-4o-mini"                   # Fast for checks
#     }
    
#     @classmethod
#     def get_model_for_task(cls, task_type: str, user_tier: str = "free"):
#         if user_tier == "pro":
#             return cls.MODELS.get(task_type, "gpt-4-turbo-preview")
#         return "gpt-4o-mini"  # Free tier fallback

class PromptOpenAI:
    def __init__(self, model: str = "gpt-4o-mini", api_key: str = settings.openai_api_key, url: str = "https://api.openai.com/v1", is_anthropic: bool = False, is_google: bool = False):
        
        # Initialize Claude client if anthropic_api_key is available
        self.client = None
        if is_anthropic and hasattr(settings, 'anthropic_api_key') and settings.anthropic_api_key:
            self.client = Anthropic(api_key=settings.anthropic_api_key)
        elif is_google and hasattr(settings, 'google_api_key') and settings.google_api_key:
            self.client = OpenAI(api_key=settings.google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
        else:
            self.client = OpenAI(api_key=api_key, base_url=url)
        self.model = model
        self.max_retries = 3
        self.max_completion_tokens = 10000
        self.url = url
    
    def set_model(self, model: str):
        self.model = model
    
    def set_max_retries(self, max_retries: int):
        self.max_retries = max_retries

    def set_max_completion_tokens(self, max_completion_tokens: int):
        self.max_completion_tokens = max_completion_tokens

    def set_url(self, url: str):
        self.url = url

    def call_openai_api(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = "gpt-4o-mini") -> str:
        """Call OpenAI API with retry logic and return raw string content."""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending request to OpenAI (attempt {attempt + 1}/{self.max_retries})")
                if system_prompt is None or system_prompt == "":
                    message = [
                        {"role": "user", "content": user_prompt}
                    ]
                else:
                    message = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                if model == "gpt-5-mini" or model == "gpt-5":
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=message,
                        max_completion_tokens=self.max_completion_tokens,
                        reasoning_effort="medium"
                    )
                else:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=message,
                        temperature=temperature,
                        max_tokens=self.max_completion_tokens
                    )
                logger.info("OpenAI API call successful")
                # Return raw assistant content for downstream code extraction
                # Get actual token usage
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                return response.choices[0].message.content, usage
            
            except OpenAIError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠ OpenAI API call failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                    logger.info(f"Retrying in next attempt...")
                    continue
                logger.error(f"✗ All retry attempts exhausted. Final error: {str(e)}")
                raise

    def call_openai_api_structured(self, system_prompt: str, user_prompt: str, response_format: dict, model: str = "gpt-4o-mini", raw=False) -> tuple:
        """Call OpenAI API with retry logic - returns (parsed_response, usage_info)"""
        json_format = response_format if not raw else {
            "type": "json_schema",
            "json_schema": {
                "name": response_format.__class__.__name__,
                "schema": response_format.model_json_schema()
            }
        }
        model = model if model != "gpt-4o-mini" else self.model
        for attempt in range(self.max_retries):
            try:
                if model == "gpt-5-mini" or model == "gpt-5":
                    response = self.client.beta.chat.completions.parse(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_completion_tokens=self.max_completion_tokens,
                        response_format=json_format
                    )
                elif model == "o4-mini" or model == "o3-mini":
                    response = self.client.beta.chat.completions.parse(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_completion_tokens=self.max_completion_tokens,
                        response_format=json_format
                    )
                else:
                    response = self.client.beta.chat.completions.parse(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=self.max_completion_tokens,
                        response_format=json_format
                    )
                
                # Get actual token usage
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                
                logger.info(
                    f"✓ OpenAI API call successful | "
                    f"Prompt: {usage['prompt_tokens']} tokens | "
                    f"Completion: {usage['completion_tokens']} tokens | "
                    f"Total: {usage['total_tokens']} tokens"
                )
                
                return response.choices[0].message.parsed, usage

            except OpenAIError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠ OpenAI API call failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                    logger.info(f"Retrying in next attempt...")
                    continue
                logger.error(f"✗ All retry attempts exhausted. Final error: {str(e)}")
                raise

    def call_claude_api(self, system_prompt, user_prompt: str, temperature: float = 0.7, model: str = "claude-sonnet-4-5-20250929") -> tuple:
        """Call Claude API with retry logic and return raw string content and usage info.

        Args:
            system_prompt: Can be a string or list (for prompt caching)
            user_prompt: User message as string
            temperature: Sampling temperature
            model: Claude model name
        """
        if self.client is None:
            raise ValueError("Claude client is not initialized. Please set anthropic_api_key in settings.")

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending request to Claude (attempt {attempt + 1}/{self.max_retries})")

                # Prepare messages
                messages = [{"role": "user", "content": user_prompt}]

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

                response = self.client.messages.create(**request_params)

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
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }

                return content, usage

            except AnthropicError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠ Claude API call failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                    logger.info(f"Retrying in next attempt...")
                    continue
                logger.error(f"✗ All retry attempts exhausted. Final error: {str(e)}")
                raise
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠ Claude API call failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                    logger.info(f"Retrying in next attempt...")
                    continue
                logger.error(f"✗ All retry attempts exhausted. Final error: {str(e)}")
                raise

    def call_claude_api_structured(self, system_prompt, user_prompt: str, response_format: dict, model: str = "claude-sonnet-4-5") -> tuple:
        """Call Claude API with structured output using tool use - returns (parsed_response, usage_info)

        Args:
            system_prompt: Can be a string or list (for prompt caching)
            user_prompt: User message as string
            response_format: Pydantic model or dict schema
            model: Claude model name
        """
        if self.client is None:
            raise ValueError("Claude client is not initialized. Please set anthropic_api_key in settings.")

        # Check if response_format is a Pydantic model or dict
        if hasattr(response_format, 'model_json_schema'):
            schema = response_format.model_json_schema()
            schema_name = response_format.__class__.__name__
        else:
            schema = response_format
            schema_name = "response"

        # Create a tool definition for structured output
        tools = [{
            "name": "provide_structured_response",
            "description": f"Provide a structured response in the format: {schema_name}",
            "input_schema": schema
        }]

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending structured request to Claude (attempt {attempt + 1}/{self.max_retries})")

                messages = [{"role": "user", "content": user_prompt}]

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

                response = self.client.messages.create(**request_params)

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
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }

                logger.info(
                    f"✓ Claude API call successful | "
                    f"Prompt: {usage['prompt_tokens']} tokens | "
                    f"Completion: {usage['completion_tokens']} tokens | "
                    f"Total: {usage['total_tokens']} tokens"
                )

                # If response_format is a Pydantic model, parse the output
                if hasattr(response_format, 'model_validate'):
                    parsed_output = response_format.model_validate(structured_output)
                    return parsed_output, usage
                else:
                    return structured_output, usage

            except AnthropicError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠ Claude API call failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                    logger.info(f"Retrying in next attempt...")
                    continue
                logger.error(f"✗ All retry attempts exhausted. Final error: {str(e)}")
                raise
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠ Claude API call failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                    logger.info(f"Retrying in next attempt...")
                    continue
                logger.error(f"✗ All retry attempts exhausted. Final error: {str(e)}")
                raise
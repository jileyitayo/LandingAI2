from openai import OpenAI, OpenAIError
from app.config import settings
import logging
logger = logging.getLogger(__name__)

class PromptOpenAI:
    def __init__(self, model: str = "gpt-4o-mini", api_key: str = settings.openai_api_key, url: str = "https://api.openai.com/v1"):
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
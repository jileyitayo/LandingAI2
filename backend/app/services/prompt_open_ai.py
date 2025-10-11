from openai import OpenAI, OpenAIError
from app.config import settings
import logging
logger = logging.getLogger(__name__)

class PromptOpenAI:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model
        self.max_retries = 3
    
    def set_model(self, model: str):
        self.model = model
    
    def set_max_retries(self, max_retries: int):
        self.max_retries = max_retries
    
    def call_openai_api(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """Call OpenAI API with retry logic"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending request to OpenAI (attempt {attempt + 1}/{self.max_retries})")
                if self.model == "gpt-5-mini" or self.model == "gpt-5":
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_completion_tokens=10000,
                        reasoning_effort="medium",
                        response_format={"type": "json_object"}
                    )
                else:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=temperature,
                        max_tokens=10000,
                        response_format={"type": "json_object"}
                    )
                
                logger.info(f"OpenAI API call successful (tokens used: ~{len(response.choices[0].message.content) // 4})")
                return response.choices[0].message.content
                
            except OpenAIError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠ OpenAI API call failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                    logger.info(f"Retrying in next attempt...")
                    continue
                logger.error(f"✗ All retry attempts exhausted. Final error: {str(e)}")
                raise

    def call_openai_api_structured(self, system_prompt: str, user_prompt: str, response_format: dict) -> str:
        """Call OpenAI API with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if self.model == "gpt-5-mini" or self.model == "gpt-5":
                    response = self.client.beta.chat.completions.parse(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_completion_tokens=10000,
                        reasoning_effort="medium",
                        response_format=response_format
                    )
                else:
                    response = self.client.beta.chat.completions.parse(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=10000,
                        response_format=response_format
                    )
                
                logger.info(f"OpenAI API call successful (tokens used: ~{len(response.choices[0].message.content) // 4})")
                return response.choices[0].message.parsed
                
            except OpenAIError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠ OpenAI API call failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                    logger.info(f"Retrying in next attempt...")
                    continue
                logger.error(f"✗ All retry attempts exhausted. Final error: {str(e)}")
                raise
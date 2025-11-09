from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
from app.services.prompt_open_ai import PromptOpenAI
load_dotenv()
def simple_openai_call(prompt: str, model: str = "gpt-4o-mini") -> str:
    """
    Makes a simple call to OpenAI's gpt-4-turbo-preview model.

    Args:
        prompt (str): The input prompt to send to the model.

    Returns:
        str: The assistant's reply.
    """
    prompt_open_ai = PromptOpenAI()
    prompt_open_ai.set_max_completion_tokens(100)
    reply, usage = prompt_open_ai.call_openai_api(system_prompt="You are a helpful assistant.", user_prompt=prompt, model=model,)
    return reply, usage


def simple_gemini_flash_call(prompt: str, model: str = "gemini-2.5-flash") -> str:
    """
    Makes a simple call to Gemini Flash model.

    Args:
        prompt (str): The input prompt to send to the model.

    Returns:
        str: The assistant's reply.
    """
    prompt_open_ai = PromptOpenAI( is_google=True)
    prompt_open_ai.set_max_completion_tokens(100)
    reply, usage = prompt_open_ai.call_openai_api(system_prompt="You are a helpful assistant. Keep your responses concise and to the point within 100 tokens.", user_prompt=prompt, model=model,)
    return reply, usage


def simple_anthropic_call(prompt: str, model: str = "claude-sonnet-4-5") -> str:
    """
    Makes a simple call to Anthropic model.

    Args:
        prompt (str): The input prompt to send to the model.

    Returns:
        str: The assistant's reply.
    """
    prompt_open_ai = PromptOpenAI( is_anthropic=True)
    prompt_open_ai.set_max_completion_tokens(100)
    reply, usage = prompt_open_ai.call_claude_api(system_prompt="You are a helpful assistant. Keep your responses concise and to the point within 100 tokens.", user_prompt=prompt, model=model,)
    return reply, usage

# if __name__ == "__main__":
#     user_prompt = "Explain the difference between supervised and unsupervised learning."
#     reply = "Nothing yet..."
#     usage = None
#     try:    
#         reply, usage = simple_gemini_flash_call(user_prompt, model="gemini-2.5-pro")
#         print(f"Gemini Flash Reply: {reply}")
#         print(f"Gemini Flash Usage: {usage}")
#         # reply, usage = simple_anthropic_call(user_prompt, model="claude-sonnet-4-5" )
#         # print(f"Anthropic Reply: {reply}")
#         # print(f"Anthropic Usage: {usage}")
#         # reply, usage = simple_openai_call(user_prompt, model="gpt-5-mini")
#         # print(f"OpenAI Reply: {reply}")
#         # print(f"OpenAI Usage: {usage}")
#     except Exception as e:
#         print(f"Error: {e}")
#     # print(f"Reply: {reply}")
#     # print(f"Usage: {usage}")

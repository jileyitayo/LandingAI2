from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
load_dotenv()
def simple_gpt4_turbo_preview_call(prompt: str) -> str:
    """
    Makes a simple call to OpenAI's gpt-4-turbo-preview model.

    Args:
        prompt (str): The input prompt to send to the model.

    Returns:
        str: The assistant's reply.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_completion_tokens=256
    )
    return response.choices[0].message.content

    # response = client.responses.create(
    #     model="gpt-5-codex",
    #     input="Generate a random Unsplash image URL for event planning."
    # )

    # print(response.output[0].content[0].text)

if __name__ == "__main__":
    user_prompt = "Explain the difference between supervised and unsupervised learning."
    reply = "Nothing yet..."
    try:    
        reply = simple_gpt4_turbo_preview_call(user_prompt)
    except Exception as e:
        print(f"Error: {e}")
    print(f"Reply: {reply}")

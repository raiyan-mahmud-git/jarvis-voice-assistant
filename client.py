import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

completion = client.chat.completions.create(
    model=os.getenv("AI_MODEL", "llama-3.3-70b-versatile"),
    messages=[
        {"role": "system", "content": "You are Jarvis, a polite British AI assistant."},
        {"role": "user", "content": "Say hello in one short sentence."},
    ],
)

print(completion.choices[0].message.content)
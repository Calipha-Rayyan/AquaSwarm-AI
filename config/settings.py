import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = "openai/openai/gpt-oss-120b"

GROQ_LLM = LLM(
    model=GROQ_MODEL,
    custom_openai=True,
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY,
    temperature=0.2,
)
"""
LLM Provider Configurations
u can refer to: https://docs.crewai.com/concepts/llms
"""
from crewai import LLM
from dotenv import load_dotenv
import os

load_dotenv()

# OpenRouter platform models (All models included paid and free)
# u can refer to: https://openrouter.ai/models
# =============================================================================
orouter = LLM(
    model="openrouter/nvidia/nemotron-nano-9b-v2:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Hugging Face platform models (Open Source)
# u can refer to: https://huggingface.co/models
# =============================================================================
hf = LLM(
    model="huggingface/Qwen/Qwen3-VL-8B-Instruct:novita"
)

# Google AI Studio platform models (Gemini)
# u can refer to: https://ai.google.dev/
# =============================================================================
gm = LLM(
    model="gemini/gemini-2.5-flash",
    temperature=0.7
)

# main/llm_clients/claude_client.py
from main.llm_clients.llm_client_interface import LLMClient
from anthropic import AsyncAnthropic
from main.config_loader import config_loader
from dotenv import load_dotenv
import os

load_dotenv()

class ClaudeClient(LLMClient):
    """Client for Anthropic Claude API"""

    def __init__(self):
        # Prefer explicit config, fall back to environment variable
        self.api_key = config_loader.get("claude.api_key", os.environ.get("ANTHROPIC_API_KEY"))
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.model = config_loader.get("claude.model_name", "claude-3-5-sonnet-latest")

    async def generate_completion(self, user_messages, max_tokens=500, temperature=0.7, top_p=0.9):
        try:
            response = await self.client.messages.create(
                model=self.model,
                messages=user_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            return response.content
        except Exception as e:
            print(f"Error with Anthropic Claude API: {e}")
            return "Fallback: Unable to generate response."

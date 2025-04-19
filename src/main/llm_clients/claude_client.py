from main.llm_clients.llm_client_interface import LLMClient
from anthropic import AsyncAnthropic
from main.config_loader import config_loader
from dotenv import load_dotenv
import os
from langfuse.decorators import observe

load_dotenv()

class ClaudeClient(LLMClient):
    """Client for the Anthropic Claude Messages API"""

    def __init__(self):
        self.api_key = config_loader.get(
            "claude.api_key", os.environ.get("ANTHROPIC_API_KEY")
        )
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.model = config_loader.get(
            "claude.model_name", "claude-3-5-sonnet-latest"
        )

    @observe
    async def generate_completion(
        self, user_messages, max_tokens=500, temperature=0.7, top_p=0.9
    ):
        # Extract top‑level system prompt; omit if none
        system_msgs = [m["content"] for m in user_messages if m.get("role") == "system"]
        system_prompt = system_msgs[0] if system_msgs else None

        # Conversation without system entries
        convo = [m for m in user_messages if m.get("role") != "system"]

        try:
            # Prepare parameters for new Messages API
            params = {
                "model": self.model,
                "messages": convo,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stream": False,
            }
            if system_prompt:
                params["system"] = system_prompt

            # Use Messages API if available
            if hasattr(self.client, "messages"):
                resp = await self.client.messages.create(**params)

                # Join all TextBlock.text into one string
                # resp.content is a list[TextBlock]
                pieces = [block.text for block in resp.content]
                return "".join(pieces)

            # Fallback for older Anthropic SDK versions
            from anthropic import HUMAN_PROMPT, AI_PROMPT
            prompt = ""
            if system_prompt:
                prompt += f"{HUMAN_PROMPT}{system_prompt}\n"
            for msg in convo:
                token = HUMAN_PROMPT if msg["role"] == "user" else AI_PROMPT
                prompt += f"{token}{msg['content']}\n"
            fallback = await self.client.completions.create(
                model=self.model,
                prompt=prompt,
                max_tokens_to_sample=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            return fallback.completion

        except Exception as e:
            # Propagate full error for debugging
            raise RuntimeError(f"ClaudeClient failed: {e}") from e

import os
from openai import OpenAI


class OpenRouterClient:
    def __init__(self) -> None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not set in environment.")

        self.model = os.getenv("OPENROUTER_MODEL", "openrouter/free")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        # Optional but useful for OpenRouter rankings/analytics
        self.extra_headers = {
            "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost:8000"),
            "X-Title": os.getenv("OPENROUTER_APP_NAME", "AI Deal Flow OS"),
        }

    def generate(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=0.2,
            extra_headers=self.extra_headers,
        )
        return response.output_text
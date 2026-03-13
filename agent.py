import sys
import json
import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    llm_api_key: str
    llm_api_base: str = "https://openrouter.ai/api/v1"
    llm_model: str = "meta-llama/llama-3.3-70b-instruct:free"

    model_config = SettingsConfigDict(env_file=".env.agent.secret", env_file_encoding="utf-8", extra="ignore")

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run agent.py \"<question>\"", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]

    try:
        settings = Settings()
    except Exception as e:
        print(f"Error loading settings: {e}", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "user", "content": question}
        ]
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{settings.llm_api_base}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            answer = data["choices"][0]["message"]["content"]
            
            output = {
                "answer": answer,
                "tool_calls": []
            }
            print(json.dumps(output))

    except httpx.HTTPStatusError as e:
        print(f"API Error: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

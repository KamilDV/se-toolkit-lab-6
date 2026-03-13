# Agent Architecture

## Overview
This agent is a CLI tool that connects to an LLM to answer user questions. It is built as part of a software engineering lab to demonstrate the integration of LLMs into software systems.

## Components
- **CLI Entry Point (`agent.py`):** Handles command-line arguments and orchestrates the request-response cycle.
- **LLM Integration:** Uses the OpenRouter API (OpenAI-compatible) to send questions to a specified model.
- **Environment Management:** Uses `pydantic-settings` to load sensitive configuration (like API keys) from a `.env.agent.secret` file.

## Data Flow
1. User provides a question as a CLI argument.
2. The agent loads the LLM configuration from environment variables.
3. The agent sends a POST request to the LLM's chat completions endpoint.
4. The agent parses the JSON response from the LLM.
5. The agent outputs a single JSON line containing the `answer` and `tool_calls` to stdout.

## Configuration
The following environment variables are required (stored in `.env.agent.secret`):
- `LLM_API_KEY`: Your API key for the LLM provider (e.g., OpenRouter).
- `LLM_API_BASE`: The base URL for the LLM API (default: `https://openrouter.ai/api/v1`).
- `LLM_MODEL`: The model name to use (default: `meta-llama/llama-3.3-70b-instruct:free`).

## Usage
To run the agent:
```bash
uv run agent.py "What does REST stand for?"
```

## Output Format
The agent outputs a single JSON line to stdout:
```json
{"answer": "Representational State Transfer.", "tool_calls": []}
```
All debug and error information is sent to stderr.

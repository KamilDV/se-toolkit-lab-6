# Agent Architecture

## Overview
This agent is a CLI tool that connects to an LLM to answer user questions. It is built as part of a software engineering lab to demonstrate the integration of LLMs into software systems.

## Components
- **CLI Entry Point (`agent.py`):** Handles command-line arguments and orchestrates the request-response cycle.
- **Agentic Loop:** Implements an iterative process where the agent can call tools, observe results, and reason about the next step (up to 10 iterations).
- **Tools:**
  - `list_files(path)`: Lists entries in a directory (restricted to project root).
  - `read_file(path)`: Reads content of a file (restricted to project root).
  - `query_api(method, path, body)`: Calls the deployed backend API with authentication.
- **LLM Integration:** Uses the OpenRouter API (OpenAI-compatible) with tool-calling support.
- **Environment Management:** Uses `pydantic-settings` to load sensitive configuration from multiple `.secret` files.

## Data Flow
1. User provides a question as a CLI argument.
2. The agent initializes the conversation with a system prompt and the user's question.
3. The agent enters a loop:
   a. Sends the current conversation and tool definitions (including `query_api`) to the LLM.
   b. If the LLM requests tool calls, the agent executes them locally (or via HTTP for `query_api`) and appends the results.
   c. If the LLM provides a final answer, the loop terminates.
4. The agent extracts the source reference from the LLM's response.
5. The agent outputs a single JSON line containing `answer`, `source`, and the full `tool_calls` log.

## Security
- **Path Validation:** Tools validate that requested paths are within the project's root directory.
- **Authentication:** `query_api` uses `LMS_API_KEY` for Bearer authentication with the backend.

## Benchmark Results
The agent was evaluated against a benchmark of 10 questions covering wiki lookup, system facts, and data queries.
Initial score: 0/10 (before implementation).
Final score: 10/10 (target).
Lessons learned:
- Clear tool descriptions are crucial for the LLM to choose the right tool.
- The system prompt must explicitly mention the availability of the live API for data-dependent questions.
- Handling `None` content in messages with `tool_calls` prevents crashes.

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

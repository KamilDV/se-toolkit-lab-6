# Plan - Task 1: Call an LLM from Code

Build a basic CLI agent that connects to an LLM via OpenRouter and returns a structured JSON response.

## LLM Configuration
- **Provider:** OpenRouter
- **Model:** `meta-llama/llama-3.3-70b-instruct:free` (as recommended)
- **API Base:** `https://openrouter.ai/api/v1`
- **Authentication:** `LLM_API_KEY` loaded from `.env.agent.secret`

## Agent Structure
- **File:** `agent.py`
- **Dependencies:**
  - `httpx`: For making HTTP requests to the LLM API.
  - `pydantic-settings`: For loading environment variables from `.env.agent.secret`.
  - `sys`, `json`: For CLI argument parsing and JSON output.
- **Workflow:**
  1. Load environment variables.
  2. Parse the question from command-line arguments.
  3. Construct a request to the OpenRouter API.
  4. Send the request and wait for the response.
  5. Parse the LLM's response.
  6. Output the answer and an empty `tool_calls` array as a JSON line to stdout.
  7. Handle errors and timeout (60s).

## Error Handling
- Use `try...except` blocks for network errors and API errors.
- Print error messages to `stderr`.
- Exit with code 0 on success, non-zero on critical failure.

## Testing Strategy
- Create a regression test `tests/test_task_1.py`.
- The test will run `uv run agent.py "What does REST stand for?"` using `subprocess.run`.
- Verify the output is valid JSON and contains `answer` and `tool_calls`.

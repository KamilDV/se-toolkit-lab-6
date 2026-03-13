# Plan - Task 3: The System Agent

Give the agent the ability to query the deployed backend API to answer questions about the system state and data.

## New Tool: `query_api`
- **Parameters**:
  - `method` (string): HTTP method (GET, POST, etc.).
  - `path` (string): API endpoint path (e.g., `/items/`).
  - `body` (string, optional): JSON request body.
- **Authentication**: Include `Authorization: Bearer <LMS_API_KEY>` in the headers.
- **Configuration**:
  - `LMS_API_KEY`: Loaded from `.env.docker.secret`.
  - `AGENT_API_BASE_URL`: Base URL for the backend (default: `http://localhost:42002`).

## Agent Updates
- Update the tool definitions to include `query_api`.
- Update the system prompt to explain when to use `query_api` (for system facts and database queries) versus `read_file`/`list_files` (for documentation and source code).
- Ensure all configuration is read from environment variables.

## Benchmarking and Iteration
- Run `uv run run_eval.py` to evaluate the agent.
- Analyze failures and refine the system prompt or tool descriptions.
- Goal: Pass all 10 local questions.

## Documentation Updates
- Update `AGENT.md` to describe the `query_api` tool, its authentication, and the logic for choosing between documentation and system tools.
- Include a summary of the benchmark results and lessons learned.

## Testing Strategy
- Add 2 more tests to `tests/agent/test_agent.py`.
- Test 1: Ask "What framework does the backend use?" and verify it uses `read_file` or `query_api` appropriately.
- Test 2: Ask "How many items are in the database?" and verify it uses `query_api`.

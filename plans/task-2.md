# Plan - Task 2: The Documentation Agent

Extend the basic LLM agent with tools to navigate and read the project wiki, and implement an agentic loop to handle multiple tool calls.

## Tools to Implement
1. **`read_file`**:
   - Parameters: `path` (string, relative to project root).
   - Security: Validate that the path is within the project directory (no `../`).
   - Returns: File content or error message.
2. **`list_files`**:
   - Parameters: `path` (string, relative to project root).
   - Security: Validate that the path is within the project directory.
   - Returns: Newline-separated list of files or error message.

## Agentic Loop
- The agent will send the user question and tool definitions to the LLM.
- If the LLM responds with `tool_calls`:
  - Execute the requested tools.
  - Append the tool results to the conversation history.
  - Send the updated history back to the LLM.
- Continue until the LLM provides a final answer or the loop limit (10 calls) is reached.
- System prompt will guide the LLM to use `list_files` to find relevant wiki files and `read_file` to extract answers and source references.

## Output Format
- `answer`: The text provided by the LLM.
- `source`: The wiki section reference (e.g., `wiki/git-workflow.md#resolving-merge-conflicts`).
- `tool_calls`: An array of all tools called, their arguments, and results.

## Testing Strategy
- Add 2 more tests to `tests/agent/test_agent.py`.
- Test 1: Ask "How do you resolve a merge conflict?" and verify that `read_file` was used and `source` points to `wiki/git-workflow.md`.
- Test 2: Ask "What files are in the wiki?" and verify that `list_files` was used.
- Mock the file system and LLM calls in the tests to ensure stability.

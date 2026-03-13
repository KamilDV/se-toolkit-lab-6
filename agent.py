import sys
import json
import httpx
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict, Any

class Settings(BaseSettings):
    llm_api_key: str
    llm_api_base: str = "https://openrouter.ai/api/v1"
    llm_model: str = "meta-llama/llama-3.3-70b-instruct:free"

    model_config = SettingsConfigDict(env_file=".env.agent.secret", env_file_encoding="utf-8", extra="ignore")

def list_files(path: str) -> str:
    """List files and directories at a given path."""
    try:
        # Security check: no parent directory traversal
        abs_root = os.path.abspath(os.getcwd())
        target_path = os.path.abspath(os.path.join(abs_root, path))
        
        if not target_path.startswith(abs_root):
            return "Error: Access denied. Cannot access files outside the project directory."
        
        if not os.path.exists(target_path):
            return f"Error: Path {path} does not exist."
        
        if not os.path.isdir(target_path):
            return f"Error: Path {path} is not a directory."
            
        entries = os.listdir(target_path)
        return "\n".join(entries)
    except Exception as e:
        return f"Error: {e}"

def read_file(path: str) -> str:
    """Read a file from the project repository."""
    try:
        # Security check: no parent directory traversal
        abs_root = os.path.abspath(os.getcwd())
        target_path = os.path.abspath(os.path.join(abs_root, path))
        
        if not target_path.startswith(abs_root):
            return "Error: Access denied. Cannot access files outside the project directory."
            
        if not os.path.exists(target_path):
            return f"Error: File {path} does not exist."
        
        if os.path.isdir(target_path):
            return f"Error: Path {path} is a directory."
            
        with open(target_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

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

    system_prompt = (
        "You are a helpful assistant. Use the provided tools to answer the user's question. "
        "Use 'list_files' to discover files in the 'wiki' directory and 'read_file' to read their content. "
        "When providing an answer based on a wiki file, include the source reference in the 'source' field "
        "using the format 'wiki/file.md#section-anchor'."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files and directories at a given path.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "The directory path to list."}
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file from the project repository.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "The path to the file to read."}
                    },
                    "required": ["path"]
                }
            }
        }
    ]

    tool_calls_log = []
    
    try:
        with httpx.Client(timeout=60.0) as client:
            for _ in range(10): # Max 10 tool calls
                payload = {
                    "model": settings.llm_model,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto"
                }
                
                response = client.post(
                    f"{settings.llm_api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.llm_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                message = data["choices"][0]["message"]
                messages.append(message)
                
                if not message.get("tool_calls"):
                    # Final answer
                    content = message.get("content") or ""
                    
                    # Extract source if present in the answer or as a separate field
                    # For Task 2, we need a separate JSON field.
                    # We'll try to find the source in the content if the LLM followed the prompt.
                    source = ""
                    # Simple heuristic: look for wiki/... in the text
                    import re
                    match = re.search(r"wiki/[a-zA-Z0-9\-\.]+(?:#[a-zA-Z0-9\-\.]+)?", content)
                    if match:
                        source = match.group(0)
                        # Remove source from the final answer text if it's there
                        # content = content.replace(source, "").strip()
                    
                    output = {
                        "answer": content,
                        "source": source,
                        "tool_calls": tool_calls_log
                    }
                    print(json.dumps(output))
                    return

                # Execute tool calls
                for tool_call in message["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    function_args = json.loads(tool_call["function"]["arguments"])
                    
                    if function_name == "list_files":
                        result = list_files(function_args.get("path", "."))
                    elif function_name == "read_file":
                        result = read_file(function_args.get("path", ""))
                    else:
                        result = f"Error: Unknown tool {function_name}"
                        
                    tool_calls_log.append({
                        "tool": function_name,
                        "args": function_args,
                        "result": result
                    })
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": function_name,
                        "content": result
                    })

            # If we hit the limit
            print(json.dumps({
                "answer": "Error: Maximum tool calls reached.",
                "source": "",
                "tool_calls": tool_calls_log
            }))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

import sys
import json
import httpx
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict, Any
import re

class Settings(BaseSettings):
    llm_api_key: str
    llm_api_base: str = "https://openrouter.ai/api/v1"
    llm_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    lms_api_key: Optional[str] = None
    agent_api_base_url: str = "http://localhost:42002"

    model_config = SettingsConfigDict(
        env_file=(".env.agent.secret", ".env.docker.secret"), 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

def list_files(path: str) -> str:
    """List files and directories at a given path."""
    try:
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

def query_api(method: str, path: str, body: Optional[str] = None, settings: Settings = None) -> str:
    """Call the deployed backend API."""
    if settings is None:
        return "Error: Settings not provided."
        
    url = f"{settings.agent_api_base_url.rstrip('/')}/{path.lstrip('/')}"
    headers = {}
    if settings.lms_api_key:
        headers["Authorization"] = f"Bearer {settings.lms_api_key}"
        
    try:
        with httpx.Client(timeout=30.0) as client:
            if method.upper() == "GET":
                response = client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = client.post(url, headers=headers, content=body)
            elif method.upper() == "PUT":
                response = client.put(url, headers=headers, content=body)
            elif method.upper() == "DELETE":
                response = client.delete(url, headers=headers)
            else:
                return f"Error: Unsupported method {method}"
                
            return json.dumps({
                "status_code": response.status_code,
                "body": response.text
            })
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
        "You are a helpful system agent. You have access to the project documentation and its live backend API. "
        "Use 'list_files' and 'read_file' to explore the project structure and documentation (in 'wiki/' or source code). "
        "Use 'query_api' to interact with the live backend for data-dependent questions or system facts. "
        "If a question requires specific data (e.g., number of items), use 'query_api' to fetch it. "
        "When providing an answer based on documentation, include the source reference in the format 'wiki/file.md#anchor'. "
        "If you use multiple tools, show your reasoning between calls."
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
        },
        {
            "type": "function",
            "function": {
                "name": "query_api",
                "description": "Call the deployed backend API.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"], "description": "HTTP method."},
                        "path": {"type": "string", "description": "The API endpoint path (e.g., '/items/')."},
                        "body": {"type": "string", "description": "Optional JSON request body."}
                    },
                    "required": ["method", "path"]
                }
            }
        }
    ]

    tool_calls_log = []
    
    try:
        with httpx.Client(timeout=60.0) as client:
            for _ in range(10):
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
                    content = message.get("content") or ""
                    source = ""
                    match = re.search(r"wiki/[a-zA-Z0-9\-\.]+(?:#[a-zA-Z0-9\-\.]+)?", content)
                    if match:
                        source = match.group(0)
                    
                    output = {
                        "answer": content,
                        "source": source,
                        "tool_calls": tool_calls_log
                    }
                    print(json.dumps(output))
                    return

                for tool_call in message["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    function_args = json.loads(tool_call["function"]["arguments"])
                    
                    if function_name == "list_files":
                        result = list_files(function_args.get("path", "."))
                    elif function_name == "read_file":
                        result = read_file(function_args.get("path", ""))
                    elif function_name == "query_api":
                        result = query_api(
                            function_args.get("method", "GET"),
                            function_args.get("path", "/"),
                            function_args.get("body"),
                            settings
                        )
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

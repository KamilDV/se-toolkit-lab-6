import subprocess
import json
import pytest
import os
import http.server
import threading
import time

class MockLLMServer(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = {
            "choices": [
                {
                    "message": {
                        "content": "Representational State Transfer."
                    }
                }
            ]
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def log_message(self, format, *args):
        return

@pytest.fixture(scope="module")
def mock_server():
    server = http.server.HTTPServer(('localhost', 42000), MockLLMServer)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield "http://localhost:42000"
    server.shutdown()

def test_agent_task_1(mock_server):
    env = os.environ.copy()
    env["LLM_API_KEY"] = "dummy"
    env["LLM_API_BASE"] = mock_server
    env["LLM_MODEL"] = "dummy-model"
    
    # We use -c to ignore the .env.agent.secret if it exists, but agent.py 
    # uses pydantic-settings which will try to load it. 
    # To be safe, we'll provide environment variables directly which take precedence.
    
    result = subprocess.run(
        ["python3", "agent.py", "What does REST stand for?"],
        capture_output=True,
        text=True,
        env=env
    )
    
    assert result.returncode == 0
    try:
        output = json.loads(result.stdout)
        assert "answer" in output
        assert "tool_calls" in output
        assert output["answer"] == "Representational State Transfer."
        assert output["tool_calls"] == []
    except json.JSONDecodeError:
        pytest.fail(f"Output is not valid JSON: {result.stdout}")

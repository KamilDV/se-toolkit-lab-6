import subprocess
import json
import unittest
import os
import http.server
import threading
import time

class MockLLMServer(http.server.BaseHTTPRequestHandler):
    responses = []
    current_response_index = 0

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        if self.current_response_index < len(self.responses):
            response = self.responses[self.current_response_index]
            self.current_response_index += 1
        else:
            response = {
                "choices": [
                    {
                        "message": {
                            "content": "No more responses planned in mock."
                        }
                    }
                ]
            }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def log_message(self, format, *args):
        return

class TestAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(('localhost', 42002), MockLLMServer)
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()
        cls.mock_url = "http://localhost:42002"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_agent_task_1(self):
        MockLLMServer.responses = [
            {
                "choices": [
                    {
                        "message": {
                            "content": "Representational State Transfer."
                        }
                    }
                ]
            }
        ]
        MockLLMServer.current_response_index = 0
        
        env = os.environ.copy()
        env["LLM_API_KEY"] = "dummy"
        env["LLM_API_BASE"] = self.mock_url
        env["LLM_MODEL"] = "dummy-model"
        
        result = subprocess.run(
            ["python3", "agent.py", "What does REST stand for?"],
            capture_output=True,
            text=True,
            env=env
        )
        
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(output["answer"], "Representational State Transfer.")
        self.assertEqual(output["tool_calls"], [])

    def test_agent_task_2_merge_conflict(self):
        MockLLMServer.responses = [
            {
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "read_file",
                                        "arguments": json.dumps({"path": "wiki/git-workflow.md"})
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {
                            "content": "To resolve a merge conflict, edit the file and commit. Source: wiki/git-workflow.md#resolving-merge-conflicts"
                        }
                    }
                ]
            }
        ]
        MockLLMServer.current_response_index = 0
        
        os.makedirs("wiki", exist_ok=True)
        with open("wiki/git-workflow.md", "w") as f:
            f.write("# Git Workflow\n## Resolving merge conflicts\nSteps...")

        env = os.environ.copy()
        env["LLM_API_KEY"] = "dummy"
        env["LLM_API_BASE"] = self.mock_url
        env["LLM_MODEL"] = "dummy-model"
        
        result = subprocess.run(
            ["python3", "agent.py", "How do you resolve a merge conflict?"],
            capture_output=True,
            text=True,
            env=env
        )
        
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertIn("resolve", output["answer"].lower())
        self.assertEqual(output["source"], "wiki/git-workflow.md#resolving-merge-conflicts")
        self.assertEqual(len(output["tool_calls"]), 1)
        self.assertEqual(output["tool_calls"][0]["tool"], "read_file")

    def test_agent_task_2_list_files(self):
        MockLLMServer.responses = [
            {
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_2",
                                    "type": "function",
                                    "function": {
                                        "name": "list_files",
                                        "arguments": json.dumps({"path": "wiki"})
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {
                            "content": "The wiki contains git-workflow.md and architecture.md."
                        }
                    }
                ]
            }
        ]
        MockLLMServer.current_response_index = 0
        
        env = os.environ.copy()
        env["LLM_API_KEY"] = "dummy"
        env["LLM_API_BASE"] = self.mock_url
        env["LLM_MODEL"] = "dummy-model"
        
        result = subprocess.run(
            ["python3", "agent.py", "What files are in the wiki?"],
            capture_output=True,
            text=True,
            env=env
        )
        
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(len(output["tool_calls"]), 1)
        self.assertEqual(output["tool_calls"][0]["tool"], "list_files")
        self.assertIn("git-workflow.md", output["tool_calls"][0]["result"])

if __name__ == "__main__":
    unittest.main()

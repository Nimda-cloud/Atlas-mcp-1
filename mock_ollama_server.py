#!/usr/bin/env python3
"""
Mock Ollama Server for testing
Provides the same API as Ollama but with mock responses
"""

import json
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Mock Ollama Server", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Mock Ollama Server"}

@app.post("/api/generate")
async def generate(request: dict):
    """Mock the Ollama generate endpoint"""
    model = request.get("model", "gpt-oss:latest")
    prompt = request.get("prompt", "")
    
    # Generate a mock response based on the prompt
    if "plan" in prompt.lower() and "task" in prompt.lower():
        response = """
{
  "plan": {
    "title": "Execute the requested task",
    "subtasks": [
      {
        "id": "subtask_1",
        "title": "Analyze the task requirements",
        "type": "automation", 
        "complexity": "low",
        "dependencies": [],
        "details": "Break down the user's request into actionable steps"
      },
      {
        "id": "subtask_2", 
        "title": "Execute the main action",
        "type": "automation",
        "complexity": "medium", 
        "dependencies": ["subtask_1"],
        "details": "Perform the primary task using available tools"
      },
      {
        "id": "subtask_3",
        "title": "Verify completion",
        "type": "automation",
        "complexity": "low",
        "dependencies": ["subtask_2"], 
        "details": "Check that the task was completed successfully"
      }
    ]
  }
}
"""
    elif "execute" in prompt.lower():
        response = "I will execute the task step by step using the available automation tools. First, I'll analyze what needs to be done, then perform the required actions, and finally verify the results."
    else:
        response = f"I understand the request: {prompt[:100]}... I will help you accomplish this task using the available tools and capabilities."
    
    return {
        "model": model,
        "created_at": "2024-08-26T06:20:00Z",
        "response": response,
        "done": True
    }

@app.get("/api/tags")
async def list_models():
    """Mock model listing"""
    return {
        "models": [
            {
                "name": "gpt-oss:latest",
                "size": 4661224676,
                "digest": "mock",
                "details": {
                    "format": "gguf",
                    "family": "llama",
                    "families": ["llama"],
                    "parameter_size": "7B",
                    "quantization_level": "Q4_0"
                }
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=11434)
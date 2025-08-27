"""
Mock ollama module for testing
"""

import aiohttp
import json
import asyncio


class Client:
    def __init__(self, host="http://localhost:11434"):
        self.host = host
    
    async def generate(self, model, prompt, **kwargs):
        """Mock generate method"""
        # Use the mock ollama server
        url = f"{self.host}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": kwargs.get("stream", False),
            "options": kwargs.get("options", {})
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        return {"response": f"Mock response for: {prompt[:50]}..."}
        except Exception as e:
            return {"response": f"Mock response for: {prompt[:50]}..."}
    
    def list(self):
        """Mock list method - synchronous"""
        try:
            # Try to run async version if possible
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, return a future
                return asyncio.create_task(self._async_list())
            else:
                # Run in sync context
                return asyncio.run(self._async_list())
        except Exception as e:
            # Fallback to static response
            return {"models": [{"name": "gpt-oss:latest"}]}
    
    async def _async_list(self):
        """Async implementation of list"""
        try:
            url = f"{self.host}/api/tags"
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        return {"models": [{"name": "gpt-oss:latest"}]}
        except Exception as e:
            return {"models": [{"name": "gpt-oss:latest"}]}


# Global client instance
client = Client()


async def generate(model, prompt, **kwargs):
    """Standalone generate function"""
    return await client.generate(model, prompt, **kwargs)
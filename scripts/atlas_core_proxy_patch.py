"""
Patch for atlas_core.py to support MCP Proxy Mode
Adds single endpoint MCP integration through mcp-proxy
"""

# Add these imports at the top of atlas_core.py
import time
from pathlib import Path

# Add this method to AtlasCore class after load_mcp_config method:

async def load_mcp_config_proxy_mode(self):
    """Load MCP configuration in proxy mode - single endpoint aggregation"""
    proxy_url = os.getenv('ATLAS_MCP_PROXY_URL', 'http://127.0.0.1:4010')
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            payload = {
                "jsonrpc": "2.0",
                "id": "atlas_bootstrap",
                "method": "list_tools"
            }
            async with session.post(proxy_url, json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    tools = result.get('result', {}).get('tools', [])
                    
                    # Group tools by namespace for easy access
                    self.mcp_tools_cache = {}
                    for tool in tools:
                        namespace = tool['name'].split('.')[0] if '.' in tool['name'] else 'default'
                        if namespace not in self.mcp_tools_cache:
                            self.mcp_tools_cache[namespace] = []
                        self.mcp_tools_cache[namespace].append(tool)
                    
                    logger.info(f"MCP Proxy: Loaded {len(tools)} tools across {len(self.mcp_tools_cache)} namespaces")
                    for ns, tools_list in self.mcp_tools_cache.items():
                        logger.info(f"  {ns}: {len(tools_list)} tools")
                    
                    self.mcp_proxy_url = proxy_url
                    self.mcp_proxy_mode = True
                    return True
                else:
                    logger.error(f"MCP Proxy returned HTTP {resp.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"Failed to connect to MCP proxy at {proxy_url}: {e}")
        return False

async def call_mcp_tool_via_proxy(self, tool_name: str, args: dict):
    """Call MCP tool through proxy with error handling and logging"""
    if not hasattr(self, 'mcp_proxy_url'):
        raise Exception("MCP Proxy not initialized")
    
    start_time = time.time()
    payload = {
        "jsonrpc": "2.0",
        "id": f"atlas_{int(time.time() * 1000)}",
        "method": "call_tool",
        "params": {
            "name": tool_name,
            "arguments": args
        }
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(self.mcp_proxy_url, json=payload) as resp:
                duration = time.time() - start_time
                
                if resp.status == 200:
                    result = await resp.json()
                    logger.info(f"MCP Tool '{tool_name}' completed in {duration:.2f}s")
                    
                    if 'error' in result:
                        logger.warning(f"MCP Tool '{tool_name}' returned error: {result['error']}")
                        return {"error": result['error']}
                    
                    return result.get('result', {})
                else:
                    error_text = await resp.text()
                    logger.error(f"MCP Tool '{tool_name}' failed: HTTP {resp.status} - {error_text}")
                    raise Exception(f"MCP Proxy call failed: HTTP {resp.status}")
                    
    except asyncio.TimeoutError:
        logger.error(f"MCP Tool '{tool_name}' timed out after 60s")
        raise Exception("MCP tool call timed out")
    except Exception as e:
        logger.error(f"MCP Tool '{tool_name}' exception: {e}")
        raise

def get_available_mcp_tools(self):
    """Get list of available MCP tools grouped by namespace"""
    if hasattr(self, 'mcp_tools_cache'):
        return self.mcp_tools_cache
    return {}

async def check_mcp_proxy_status(self):
    """Check MCP proxy health and return status"""
    if not hasattr(self, 'mcp_proxy_url'):
        return {"status": "disabled", "mode": "direct"}
    
    try:
        timeout = aiohttp.ClientTimeout(total=3)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            payload = {
                "jsonrpc": "2.0", 
                "id": "health_check",
                "method": "list_tools"
            }
            async with session.post(self.mcp_proxy_url, json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    tools_count = len(result.get('result', {}).get('tools', []))
                    return {
                        "status": "online",
                        "mode": "proxy", 
                        "url": self.mcp_proxy_url,
                        "tools_count": tools_count,
                        "namespaces": list(self.mcp_tools_cache.keys()) if hasattr(self, 'mcp_tools_cache') else []
                    }
                else:
                    return {"status": "error", "mode": "proxy", "http_status": resp.status}
    except Exception as e:
        return {"status": "offline", "mode": "proxy", "error": str(e)}

# Modify the __init__ method to add proxy mode detection:
# Find this line in __init__:
#   self.mcp_endpoints: Dict[str, Dict[str, str]] = {}
# Add after it:
#   self.mcp_proxy_mode = os.getenv('ATLAS_MCP_PROXY_MODE', 'false').lower() == 'true'

# Modify the load_mcp_config call in __init__ or startup:
# Replace:
#   self.load_mcp_config()
# With:
#   if self.mcp_proxy_mode:
#       # Will be called async in initialize()
#       pass  
#   else:
#       self.load_mcp_config()

# Add async initialization method if not exists:
async def initialize_mcp(self):
    """Initialize MCP system (proxy or direct mode)"""
    if self.mcp_proxy_mode:
        success = await self.load_mcp_config_proxy_mode()
        if not success:
            logger.warning("Failed to initialize MCP proxy, falling back to direct mode")
            self.mcp_proxy_mode = False
            self.load_mcp_config()
    else:
        self.load_mcp_config()

# Modify existing MCP tool calling methods to use proxy when available:
# In methods that call MCP tools (like execute_tts_command), add:
# if self.mcp_proxy_mode:
#     return await self.call_mcp_tool_via_proxy(tool_name, args)
# else:
#     # existing direct call logic

# Update get_system_status method to include MCP proxy status:
# Add to the status dict:
#   "mcp": await self.check_mcp_proxy_status() if self.mcp_proxy_mode else await self.check_mcp_status()

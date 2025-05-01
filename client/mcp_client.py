import asyncio
import sys
import json
from typing import Dict, List, Optional
from mcp import ClientSession
from mcp.client.sse import sse_client

class MCPClient:
    def __init__(self, config_path: str = None):
        self.servers = {}
        self.active_sessions = {}
        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: str):
        """Load MCP server configurations from a JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.servers = config.get('mcpServers', {})
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)

    async def connect_to_server(self, server_name: str) -> Optional[ClientSession]:
        """Connect to a specific MCP server."""
        if server_name not in self.servers:
            print(f"Server '{server_name}' not found in config")
            return None

        server_config = self.servers[server_name]
        server_url = f"http://localhost:8000/sse"  # Default MCP server URL

        try:
            print(f"[*] Connecting to MCP server: {server_name}")
            streams_context = sse_client(url=server_url)
            streams = await streams_context.__aenter__()
            session_context = ClientSession(*streams)
            session = await session_context.__aenter__()
            await session.initialize()
            
            self.active_sessions[server_name] = session
            return session
        except Exception as e:
            print(f"[-] Error connecting to server {server_name}: {e}")
            return None

    async def list_tools(self, server_name: str) -> List[str]:
        """List available tools on the specified server."""
        session = self.active_sessions.get(server_name)
        if not session:
            session = await self.connect_to_server(server_name)
            if not session:
                return []

        try:
            response = await session.list_tools()
            tools = response.tools
            return [tool.name for tool in tools]
        except Exception as e:
            print(f"[-] Error listing tools: {e}")
            return []

    async def call_tool(self, server_name: str, tool_name: str, params: Dict) -> str:
        """Call a specific tool on the server with given parameters."""
        session = self.active_sessions.get(server_name)
        if not session:
            session = await self.connect_to_server(server_name)
            if not session:
                return "Failed to connect to server"

        try:
            result = await session.call_tool(tool_name, params)
            return result
        except Exception as e:
            return f"Error calling tool: {e}"

async def interactive_session():
    """Start an interactive MCP client session."""
    client = MCPClient("config.json")
    
    while True:
        try:
            command = input("\nMCP> ").strip()
            if not command:
                continue

            if command == "exit":
                break

            parts = command.split()
            if parts[0] == "list":
                if len(parts) < 2:
                    print("Usage: list <server_name>")
                    continue
                tools = await client.list_tools(parts[1])
                print(f"Available tools on {parts[1]}:")
                for tool in tools:
                    print(f"  - {tool}")

            elif parts[0] == "call":
                if len(parts) < 4:
                    print("Usage: call <server_name> <tool_name> <params_json>")
                    continue
                server_name = parts[1]
                tool_name = parts[2]
                try:
                    params = json.loads(" ".join(parts[3:]))
                except json.JSONDecodeError:
                    print("Invalid JSON parameters")
                    continue

                result = await client.call_tool(server_name, tool_name, params)
                print(f"Result: {result}")

            elif parts[0] == "help":
                print("""
Available commands:
  list <server_name>                     - List available tools on server
  call <server_name> <tool> <params>     - Call a tool with parameters
  help                                   - Show this help
  exit                                   - Exit the client
                """)
            else:
                print("Unknown command. Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting MCP Client...")
    print("Type 'help' for available commands")
    asyncio.run(interactive_session()) 
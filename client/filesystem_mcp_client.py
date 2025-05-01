import asyncio
import json
import logging
import os
from contextlib import AsyncExitStack
from typing import Any

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class Configuration:
    def __init__(self) -> None:
        self.load_env()

    @staticmethod
    def load_env() -> None:
        load_dotenv()

    @staticmethod
    def load_config(file_path: str) -> dict[str, Any]:
        with open(file_path, "r") as f:
            return json.load(f)


class Server:
    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.config = config
        self.exit_stack = AsyncExitStack()
        self.session: ClientSession | None = None

    async def initialize(self) -> None:
        server_params = StdioServerParameters(
            command=self.config["command"],
            args=self.config["args"],
            env={**os.environ, **self.config.get("env", {})}
        )
        try:
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.session = session
        except Exception as e:
            logging.error(f"Error initializing server {self.name}: {e}")
            await self.cleanup()
            raise

    async def list_tools(self) -> list[str]:
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")
        response = await self.session.list_tools()
        return [tool.name for tool in response.tools]
    
    async def call_tool(self, tool_name: str, params: dict) -> Any:
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")
        return await self.session.call_tool(tool_name, params)
    
    async def cleanup(self) -> None:
        try:
            await self.exit_stack.aclose()
            self.session = None
        except Exception as e:
            logging.error(f"Error during cleanup of server {self.name}: {e}")


async def interactive_session():
    config = Configuration()
    server_config = config.load_config("servers_config.json")
    fs_server = Server("filesystem", server_config["mcpServers"]["filesystem"])
    try:
        await fs_server.initialize()
    except Exception as e:
        print(f"[-] Could not start filesystem server: {e}")
        return
    print("Filesystem MCP Client started")
    print("Type 'help' for available commands")
    while True:
        try:
            command = input("\nFilesystem> ").strip()
            if not command:
                continue
            if command == "exit":
                break
            parts = command.split()
            if parts[0] == "list":
                if len(parts) == 1:
                    tools = await fs_server.list_tools()
                    print("Available tools:")
                    for tool in tools:
                        print(f"  - {tool}")
                else:
                    path = " ".join(parts[1:])
                    result = await fs_server.call_tool("list_directory", {"path": path})
                    print(result)
            elif parts[0] == "read":
                if len(parts) < 2:
                    print("Usage: read <file_path>")
                    continue
                path = " ".join(parts[1:])
                result = await fs_server.call_tool("get_content", {"path": path})
                print(result)
            elif parts[0] == "write":
                if len(parts) < 3:
                    print("Usage: write <file_path> <content>")
                    continue
                path = parts[1]
                content = " ".join(parts[2:])
                result = await fs_server.call_tool("write_file", {"path": path, "content": content})
                print(result)
            elif parts[0] == "delete":
                if len(parts) < 2:
                    print("Usage: delete <file_path>")
                    continue
                path = " ".join(parts[1:])
                result = await fs_server.call_tool("delete_file", {"path": path})
                print(result)
            elif parts[0] == "help":
                print("""
Available commands:
  list                    - List available tools
  list <path>            - List directory contents
  read <file_path>       - Read file contents
  write <path> <content> - Write content to file
  delete <path>          - Delete file
  help                   - Show this help
  exit                   - Exit the client
                """)
            else:
                print("Unknown command. Type 'help' for available commands.")
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
        except Exception as e:
            print(f"Error: {e}")
    await fs_server.cleanup()

if __name__ == "__main__":
    asyncio.run(interactive_session())

import os
import json
import openai
from mcp_client import MCPClient


class ChatGPTMCPClient:
    def __init__(self, openai_api_key: str, mcp_config_path: str):
        """Initialize the ChatGPT MCP client.

        Args:
            openai_api_key: OpenAI API key for ChatGPT
            mcp_config_path: Path to MCP server configuration file
        """
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.mcp_client = MCPClient(mcp_config_path)
        self.conversation_history = []

    async def process_prompt(self, prompt: str) -> str:
        """Process a prompt using ChatGPT and MCP servers.

        Args:
            prompt: User's input prompt

        Returns:
            str: ChatGPT's response
        """
        # Add system message to guide the model
        system_message = """You are an AI assistant that can interact with MCP servers.
        You can:
        1. List available tools on MCP servers
        2. Call tools on MCP servers
        3. Process the results and provide meaningful responses

        When you need to interact with MCP servers, use the following format:
        MCP_ACTION: <action_type> <server_name> [<tool_name>] [<params>]

        Available action types:
        - LIST: List tools on a server
        - CALL: Call a tool on a server

        Example:
        MCP_ACTION: LIST filesystem
        MCP_ACTION: CALL filesystem list_directory {"path": "/"}
        """

        # Add conversation history and current prompt
        messages = [
            {"role": "system", "content": system_message},
            *self.conversation_history,
            {"role": "user", "content": prompt}
        ]

        # Get response from ChatGPT
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )

        chat_response = response.choices[0].message.content

        # Check if response contains MCP actions
        if "MCP_ACTION:" in chat_response:
            # Extract MCP actions
            actions = [line.strip() for line in chat_response.split("\n") if line.strip().startswith("MCP_ACTION:")]
 
            for action in actions:
                # Parse action
                parts = action.replace("MCP_ACTION:", "").strip().split()
                action_type = parts[0]
                server_name = parts[1]

                if action_type == "LIST":
                    # List tools on server
                    tools = await self.mcp_client.list_tools(server_name)
                    chat_response += (f"\n\nAvailable tools on {server_name}:\n"
                                      + "\n".join(f"- {tool}" for tool in tools))

                elif action_type == "CALL":
                    # Call tool on server
                    tool_name = parts[2]
                    params = json.loads(" ".join(parts[3:]))
                    result = await self.mcp_client.call_tool(server_name, tool_name, params)
                    chat_response += f"\n\nTool result:\n{result}"

        # Update conversation history
        self.conversation_history.extend([
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": chat_response}
        ])

        return chat_response


async def interactive_session():
    """Start an interactive session with ChatGPT and MCP servers."""
    # Get OpenAI API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return

    # Initialize client
    client = ChatGPTMCPClient(api_key, "config.json")

    print("ChatGPT MCP Client started. Type 'exit' to quit.")
    print("You can interact with MCP servers through ChatGPT.")

    while True:
        try:
            prompt = input("\nYou: ").strip()
            if not prompt:
                continue
            if prompt.lower() == "exit":
                break

            response = await client.process_prompt(prompt)
            print(f"\nAssistant: {response}")

        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(interactive_session())

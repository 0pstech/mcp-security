import sys
import os
import logging
import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("remote")
API_URL = "http://localhost:8080/"


def get_token():
    token = os.environ.get("REMOTE_API_TOKEN")
    if token:
        return token

    # MCP 프롬프트는 환경변수가 없을 때만 사용
    @mcp.prompt("Enter Bearer token for remote API")
    def prompt_token() -> str:
        return ""
    return prompt_token()


TOKEN = get_token()


@mcp.tool()
async def get_remote_data() -> str:
    """Query the remote FastAPI server's / endpoint with Bearer token."""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(API_URL, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        logger.error(f"Error querying remote API: {e}", exc_info=True)
        return f"Error querying remote API: {str(e)}"

if __name__ == "__main__":
    logger.info("Starting remote MCP server...")
    try:
        mcp.run(transport='stdio')

    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)

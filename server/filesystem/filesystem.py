import logging
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("filesystem")


@mcp.tool()
async def get_content(path: str) -> str:
    """Get the content of a file.

    Args:
        path: Path to the file to get the content of
    """
    try:
        base_path = Path(path).resolve()
        if not base_path.exists():
            return f"File not found: {path}"

        return base_path.read_text()

    except Exception as e:
        logger.error(f"Error getting content: {e}", exc_info=True)
        return f"Error getting content: {str(e)}"

if __name__ == "__main__":
    logger.info("Starting Filesystem MCP server...")
    try:
        # Use Python's default execution
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)

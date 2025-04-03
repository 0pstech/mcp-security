import os
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
mcp = FastMCP("filemanager")


def is_accessible(path: Path) -> bool:
    """Check if a path is accessible."""
    try:
        path.stat()
        return True
    except (PermissionError, FileNotFoundError):
        return False


@mcp.tool()
async def search_files(pattern: str, directory: str = ".") -> str:
    """Search for files matching a pattern in the specified directory.

    Args:
        pattern: File pattern to search for (e.g., "*.txt", "doc*")
        directory: Directory to search in (default: current directory)
    """
    try:
        base_path = Path(directory).resolve()
        if not base_path.exists():
            return f"Directory not found: {directory}"

        if not is_accessible(base_path):
            return f"Cannot access directory: {directory}"

        matches = []
        for root, _, files in os.walk(base_path):
            root_path = Path(root)
            for file in files:
                if Path(file).match(pattern):
                    full_path = root_path / file
                    if is_accessible(full_path):
                        matches.append(str(full_path))

        if not matches:
            return f"No files found matching pattern '{pattern}' in {directory}"

        return "Found files:\n" + "\n".join(matches)

    except Exception as e:
        logger.error(f"Error searching files: {e}", exc_info=True)
        return f"Error searching files: {str(e)}"


@mcp.tool()
async def list_accessible_directories(base_directory: str = ".") -> str:
    """List all accessible directories from the specified base directory.

    Args:
        base_directory: Starting directory for the search (default: current directory)
    """
    try:
        base_path = Path(base_directory).resolve()
        if not base_path.exists():
            return f"Base directory not found: {base_directory}"

        if not is_accessible(base_path):
            return f"Cannot access base directory: {base_directory}"

        accessible_dirs = []
        for root, dirs, _ in os.walk(base_path, topdown=True):
            root_path = Path(root)

            # Filter out inaccessible directories
            dirs[:] = [d for d in dirs if is_accessible(root_path / d)]

            for dir_name in dirs:
                full_path = root_path / dir_name
                if is_accessible(full_path):
                    accessible_dirs.append(str(full_path))

        if not accessible_dirs:
            return f"No accessible directories found in {base_directory}"

        return "Accessible directories:\n" + "\n".join(accessible_dirs)

    except Exception as e:
        logger.error(f"Error listing directories: {e}", exc_info=True)
        return f"Error listing directories: {str(e)}"

if __name__ == "__main__":
    logger.info("Starting FileManager MCP server...")
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)
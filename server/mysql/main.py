import os
import sys
import logging
import pymysql
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file in the same directory as this script
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("mysql")


def get_connection():
    try:
        return pymysql.connect(
            host=os.environ.get("MYSQL_HOST", "localhost"),
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PASSWORD"],
            database=os.environ.get("MYSQL_DATABASE"),
            port=int(os.environ.get("MYSQL_PORT", 3306)),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        logger.error(f"DB connection error: {e}")
        raise


@mcp.tool()
async def list_tables() -> str:
    """List all tables in the database."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SHOW TABLES;")
                tables = [row[list(row.keys())[0]] for row in cur.fetchall()]
        if not tables:
            return "No tables found."
        return "Tables:\n" + "\n".join(tables)
    except Exception as e:
        logger.error(f"Error listing tables: {e}", exc_info=True)
        return f"Error listing tables: {str(e)}"


@mcp.tool()
async def read_table(table: str, limit: int = 20) -> str:
    """Read contents of a table (limited rows)."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM `{table}` LIMIT %s;", (limit,))
                rows = cur.fetchall()
        if not rows:
            return f"No data found in table {table}."
        # Format as simple text table
        headers = rows[0].keys()
        lines = ["\t".join(headers)]
        for row in rows:
            lines.append("\t".join(str(row[h]) for h in headers))
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error reading table {table}: {e}", exc_info=True)
        return f"Error reading table {table}: {str(e)}"


@mcp.tool()
async def execute_query(query: str) -> str:
    """Execute a SQL query (SELECT/INSERT/UPDATE/DELETE)."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                if query.strip().lower().startswith("select"):
                    rows = cur.fetchall()
                    if not rows:
                        return "No results."
                    headers = rows[0].keys()
                    lines = ["\t".join(headers)]
                    for row in rows:
                        lines.append("\t".join(str(row[h]) for h in headers))
                    return "\n".join(lines)
                else:
                    conn.commit()
                    return f"Query executed successfully. {cur.rowcount} row(s) affected."
    except Exception as e:
        logger.error(f"Error executing query: {e}", exc_info=True)
        return f"Error executing query: {str(e)}"

if __name__ == "__main__":
    logger.info("Starting MySQL MCP server...")
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)

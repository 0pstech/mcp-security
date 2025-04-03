from typing import Any, TypedDict, Optional
import httpx
import logging
import sys
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Log to stderr for better visibility
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


class NWSResponse(TypedDict):
    properties: dict[str, Any]
    features: list[dict[str, Any]]


async def make_nws_request(url: str) -> Optional[dict[str, Any]]:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return None
        except httpx.TimeoutException as e:
            print(f"Timeout occurred: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            return None


def format_alert(feature: dict[str, Any]) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return (
        f"Event: {props.get('event', 'Unknown')}\n"
        f"Area: {props.get('areaDesc', 'Unknown')}\n"
        f"Severity: {props.get('severity', 'Unknown')}\n"
        f"Description: {props.get('description', 'No description available')}\n"
        f"Instructions: {props.get('instruction', 'No specific instructions provided')}"
    )


@mcp.tool()
async def get_alerts_py(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    if not state or len(state) != 2:
        return "Invalid state code. Please provide a two-letter US state code (e.g. CA, NY)"

    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


@mcp.tool()
async def get_forecast_py(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location (-90 to 90)
        longitude: Longitude of the location (-180 to 180)
    """
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return "Invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180."

    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = (
            f"{period['name']}:\n"
            f"Temperature: {period['temperature']}°{period['temperatureUnit']}\n"
            f"Wind: {period['windSpeed']} {period['windDirection']}\n"
            f"Forecast: {period['detailedForecast']}"
        )
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

if __name__ == "__main__":
    logger.info("Starting Weather MCP server...")
    try:
        # Use Python's default execution
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)

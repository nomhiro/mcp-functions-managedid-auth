import azure.functions as func
import logging
import json
from typing import Dict, Any
from datetime import datetime, timezone
from auth.managed_id_auth import ManagedIdAuthenticator
import pytz
import random
import os

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
authenticator = ManagedIdAuthenticator()

# ---------------- Snippet MCP Tools (Azure Sample ベース) ----------------
_SNIPPET_NAME_PROPERTY_NAME = "snippetname"
_SNIPPET_PROPERTY_NAME = "snippet"
_BLOB_PATH = f"snippets/{{mcptoolargs.{_SNIPPET_NAME_PROPERTY_NAME}}}.json"


class ToolProperty:
    def __init__(self, property_name: str, property_type: str, description: str):
        self.propertyName = property_name
        self.propertyType = property_type
        self.description = description

    def to_dict(self):
        return {
            "propertyName": self.propertyName,
            "propertyType": self.propertyType,
            "description": self.description,
        }


tool_properties_save_snippets_object = [
    ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The name of the snippet."),
    ToolProperty(_SNIPPET_PROPERTY_NAME, "string", "The content of the snippet."),
]

tool_properties_get_snippets_object = [
    ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The name of the snippet."),
]

tool_properties_save_snippets_json = json.dumps([p.to_dict() for p in tool_properties_save_snippets_object])
tool_properties_get_snippets_json = json.dumps([p.to_dict() for p in tool_properties_get_snippets_object])


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="hello_mcp",
    description="Hello world.",
    toolProperties="[]",
)
def hello_mcp(context) -> str:
    return "Hello I am MCPTool!"


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="get_snippet",
    description="Retrieve a snippet by name.",
    toolProperties=tool_properties_get_snippets_json,
)
@app.generic_input_binding(arg_name="file", type="blob", connection="AzureWebJobsStorage", path=_BLOB_PATH)
def get_snippet(file: func.InputStream, context) -> str:
    try:
        snippet_content = file.read().decode("utf-8")
        logging.info(f"Retrieved snippet: {snippet_content}")
        return snippet_content
    except Exception as e:
        logging.error(f"Failed to read snippet: {e}")
        return json.dumps({"error": str(e)})


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="save_snippet",
    description="Save a snippet with a name.",
    toolProperties=tool_properties_save_snippets_json,
)
@app.generic_output_binding(arg_name="file", type="blob", connection="AzureWebJobsStorage", path=_BLOB_PATH)
def save_snippet(file: func.Out[str], context) -> str:
    try:
        data = json.loads(context)
        args = data.get("arguments", {})
        name = args.get(_SNIPPET_NAME_PROPERTY_NAME)
        content = args.get(_SNIPPET_PROPERTY_NAME)
        if not name:
            return "No snippet name provided"
        if not content:
            return "No snippet content provided"
        file.set(content)
        logging.info(f"Saved snippet '{name}'")
        return f"Snippet '{name}' saved successfully"
    except Exception as e:
        logging.error(f"Failed to save snippet: {e}")
        return json.dumps({"error": str(e)})

# MCP Tool: Get Current Time
@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="get_current_time",
    description="Get the current date and time in various formats and timezones",
    toolProperties=json.dumps({
        "timezone": {
            "type": "string",
            "description": "Timezone for the current time (e.g., 'UTC', 'Asia/Tokyo')",
            "default": "UTC"
        },
        "format": {
            "type": "string",
            "description": "Time format ('iso', 'locale', 'timestamp')",
            "enum": ["iso", "locale", "timestamp"],
            "default": "iso"
        }
    })
)
def get_current_time(context) -> str:
    """
    MCP Tool: Get current time with authentication
    """
    try:
        # Get tool arguments
        args = getattr(context, 'arguments', {}) or {}
        timezone_str = args.get("timezone", "UTC")
        format_type = args.get("format", "iso")
        
        logging.info(f'Getting current time for timezone: {timezone_str}, format: {format_type}')
        
        # Get current time
        now_utc = datetime.now(timezone.utc)
        
        # Handle timezone conversion
        if timezone_str.upper() == "UTC":
            target_time = now_utc
        else:
            try:
                tz = pytz.timezone(timezone_str)
                target_time = now_utc.astimezone(tz)
            except pytz.exceptions.UnknownTimeZoneError:
                target_time = now_utc
                timezone_str = "UTC (invalid timezone provided)"
        
        # Format time based on requested format
        if format_type == "iso":
            time_string = target_time.isoformat()
        elif format_type == "locale":
            time_string = target_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        elif format_type == "timestamp":
            time_string = str(int(target_time.timestamp()))
        else:
            time_string = target_time.isoformat()
        
        result = {
            "current_time": time_string,
            "timezone": timezone_str,
            "format": format_type,
            "utc_timestamp": int(now_utc.timestamp()),
            "day_of_week": target_time.strftime("%A"),
            "day_of_year": target_time.timetuple().tm_yday
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logging.error(f'Error in get_current_time: {e}')
        error_result = {
            "error": "Failed to get current time",
            "details": str(e)
        }
        return json.dumps(error_result, indent=2)


# MCP Tool: Get Weather Information
@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="get_weather_info",
    description="Get weather information for a specific location and date",
    toolProperties=json.dumps({
        "location": {
            "type": "string",
            "description": "Location name (city, country) or coordinates (lat,lon)",
            "default": "Tokyo,Japan"
        },
        "date": {
            "type": "string",
            "description": "Date for weather information (YYYY-MM-DD format, optional)"
        }
    })
)
def get_weather_info(context) -> str:
    """
    MCP Tool: Get weather information with authentication
    """
    try:
        # Get tool arguments
        args = getattr(context, 'arguments', {}) or {}
        location = args.get("location", "Tokyo,Japan")
        date_str = args.get("date")
        
        logging.info(f'Getting weather for location: {location}, date: {date_str}')
        
        # Parse date or use current date
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                target_date = datetime.now()
        else:
            target_date = datetime.now()
        
        # Generate mock weather data (in production, use real weather API)
        weather_data = _generate_mock_weather_data(location, target_date)
        
        return json.dumps(weather_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logging.error(f'Error in get_weather_info: {e}')
        error_result = {
            "error": "Failed to get weather information",
            "details": str(e)
        }
        return json.dumps(error_result, indent=2)


def _generate_mock_weather_data(location: str, target_date: datetime) -> Dict[str, Any]:
    """
    Generate realistic mock weather data
    """
    # Seasonal temperature ranges (approximate for Tokyo)
    month = target_date.month
    seasonal_temps = {
        1: (-2, 8), 2: (0, 10), 3: (4, 14), 4: (10, 20),
        5: (15, 25), 6: (19, 28), 7: (23, 32), 8: (25, 33),
        9: (21, 29), 10: (15, 23), 11: (8, 17), 12: (2, 12)
    }
    
    temp_min, temp_max = seasonal_temps.get(month, (10, 20))
    current_temp = random.randint(temp_min, temp_max)
    feels_like = current_temp + random.randint(-3, 3)
    
    # Weather conditions with seasonal bias
    conditions = [
        {"main": "Clear", "description": "快晴"},
        {"main": "Clouds", "description": "曇り"},
        {"main": "Rain", "description": "雨"},
        {"main": "Snow", "description": "雪"} if month in [12, 1, 2, 3] else {"main": "Clouds", "description": "薄曇り"}
    ]
    
    weather = random.choice(conditions)
    humidity = random.randint(40, 80)
    pressure = random.randint(1010, 1025)
    wind_speed = random.randint(0, 15)
    wind_direction = random.randint(0, 359)
    
    return {
        "location": location,
        "date": target_date.strftime("%Y-%m-%d"),
        "temperature": {
            "current": current_temp,
            "feels_like": feels_like,
            "min": temp_min,
            "max": temp_max,
            "unit": "°C"
        },
        "weather": weather,
        "humidity": f"{humidity}%",
        "pressure": f"{pressure} hPa",
        "wind": {
            "speed": f"{wind_speed} m/s",
            "direction": wind_direction
        },
        "forecast": {
            "tomorrow": {
                "high": current_temp + random.randint(-5, 5),
                "low": current_temp - random.randint(3, 8),
                "condition": random.choice(conditions)["description"]
            }
        },
        "last_updated": datetime.now().isoformat(),
        "data_source": "Mock Weather Service (Demo)",
        "note": "これはデモ用のモックデータです。実際の天気情報を取得するにはOPENWEATHER_API_KEY環境変数を設定してください。"
    }


# Test endpoint for Managed ID authentication
@app.route(route="test-auth", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "POST"])
async def test_auth(req: func.HttpRequest) -> func.HttpResponse:
    """
    Test Managed ID authentication endpoint
    """
    logging.info('Testing Managed ID authentication')
    
    try:
        # Check if in development environment
        is_dev = os.getenv('AZURE_FUNCTIONS_ENVIRONMENT') == 'Development'
        
        if is_dev:
            # Skip authentication in development
            auth_result = {
                "authorized": True,
                "principal": {
                    "sub": "dev-user",
                    "note": "Development mode - authentication skipped"
                }
            }
        else:
            # Authenticate request using Managed ID in production
            auth_result = await authenticator.authorize(req)
        
        return func.HttpResponse(
            json.dumps({
                "authenticated": auth_result["authorized"],
                "principal": auth_result.get("principal", {}),
                "timestamp": datetime.now().isoformat(),
                "environment": "development" if is_dev else "production",
                "message": "Authentication test successful" if auth_result["authorized"] else "Authentication failed"
            }),
            status_code=200 if auth_result["authorized"] else 401,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f'Error in authentication test: {str(e)}')
        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "details": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint
    """
    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "MCP Functions Server",
            "environment": os.getenv('AZURE_FUNCTIONS_ENVIRONMENT', 'production'),
            "mcp_tools": [
                "get_current_time",
                "get_weather_info"
            ]
        }),
        status_code=200,
        mimetype="application/json"
    )


# Simple test chat endpoint for development
@app.route(route="test-chat", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
async def test_chat(req: func.HttpRequest) -> func.HttpResponse:
    """
    Simple test chat endpoint for development
    """
    logging.info('Processing test chat request')
    
    try:
        # Check if in development environment
        is_dev = os.getenv('AZURE_FUNCTIONS_ENVIRONMENT') == 'Development'
        
        if not is_dev:
            # In production, authenticate the request
            auth_result = await authenticator.authorize(req)
            if not auth_result["authorized"]:
                return func.HttpResponse(
                    json.dumps({"error": "Unauthorized"}),
                    status_code=401,
                    mimetype="application/json"
                )
        
        # Parse request body
        try:
            req_body = req.get_json()
            if not req_body or "message" not in req_body:
                raise ValueError("Missing message in request body")
        except (ValueError, TypeError) as e:
            return func.HttpResponse(
                json.dumps({"error": f"Invalid request body: {str(e)}"}),
                status_code=400,
                mimetype="application/json"
            )
        
        message = req_body["message"].lower()
        
        # Simple mock responses for testing
        if "time" in message or "時刻" in message or "時間" in message:
            now = datetime.now()
            response_content = f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')} (Mock response for development)"
        elif "weather" in message or "天気" in message:
            response_content = "Weather: Sunny, 22°C in Tokyo (Mock response for development)"
        else:
            response_content = f"I received your message: '{req_body['message']}'. In production, this would be processed by MCP tools and Azure OpenAI."
        
        return func.HttpResponse(
            json.dumps({
                "content": response_content,
                "timestamp": datetime.now().isoformat(),
                "authenticated_user": "dev-user" if is_dev else "production-user",
                "note": "This is a test endpoint. Real MCP tools are available via MCP protocol."
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f'Error processing test chat request: {str(e)}')
        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "details": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )
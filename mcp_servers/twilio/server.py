import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv

from tools import (
    auth_token_context,
    # Messaging
    twilio_send_sms,
    twilio_send_mms,
    twilio_get_messages,
    twilio_get_message_by_sid,
    # Voice
    twilio_make_call,
    twilio_get_calls,
    twilio_get_call_by_sid,
    twilio_get_recordings,
    # Phone Numbers
    twilio_search_available_numbers,
    twilio_purchase_phone_number,
    twilio_list_phone_numbers,
    twilio_update_phone_number,
    twilio_release_phone_number,
    # Account
    twilio_get_account_info,
    twilio_get_usage_records,
    twilio_get_balance,
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

TWILIO_MCP_SERVER_PORT = int(os.getenv("TWILIO_MCP_SERVER_PORT", "5000"))

@click.command()
@click.option("--port", default=TWILIO_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses for StreamableHTTP instead of SSE streams",
)
def main(
    port: int,
    log_level: str,
    json_response: bool,
) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create the MCP server instance
    app = Server("twilio-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Messaging Tools
            types.Tool(
                name="twilio_send_sms",
                description="Send an SMS message to a phone number using Twilio. Perfect for sending text notifications, alerts, or confirmations to users.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient phone number in E.164 format (e.g., +1234567890)"
                        },
                        "from_": {
                            "type": "string", 
                            "description": "Sender phone number (must be a Twilio phone number you own)"
                        },
                        "body": {
                            "type": "string",
                            "description": "Message content (up to 1600 characters)"
                        },
                        "status_callback": {
                            "type": "string",
                            "description": "Optional webhook URL to receive delivery status updates"
                        }
                    },
                    "required": ["to", "from_", "body"]
                }
            ),
            types.Tool(
                name="twilio_send_mms",
                description="Send an MMS message with media attachments (images, videos, PDFs) using Twilio. Use this when you need to send visual content along with or instead of text.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient phone number in E.164 format"
                        },
                        "from_": {
                            "type": "string",
                            "description": "Sender phone number (must be a Twilio phone number you own)"
                        },
                        "body": {
                            "type": "string",
                            "description": "Optional message text to accompany the media"
                        },
                        "media_url": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of media URLs to attach (max 10 attachments)"
                        },
                        "status_callback": {
                            "type": "string",
                            "description": "Optional webhook URL to receive delivery status updates"
                        }
                    },
                    "required": ["to", "from_"]
                }
            ),
            types.Tool(
                name="twilio_get_messages",
                description="Retrieve a list of SMS/MMS messages from your Twilio account. Use this to check message history, delivery status, or find specific conversations.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of messages to retrieve (default 20, max 1000)",
                            "default": 20
                        },
                        "date_sent_after": {
                            "type": "string",
                            "description": "ISO date string to filter messages sent after this date (e.g., '2024-01-01')"
                        },
                        "date_sent_before": {
                            "type": "string", 
                            "description": "ISO date string to filter messages sent before this date"
                        },
                        "from_": {
                            "type": "string",
                            "description": "Filter by sender phone number"
                        },
                        "to": {
                            "type": "string",
                            "description": "Filter by recipient phone number"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="twilio_get_message_by_sid",
                description="Retrieve detailed information about a specific message using its unique SID. Use this when you need complete details about a particular message including delivery status and error information.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_sid": {
                            "type": "string",
                            "description": "Unique identifier (SID) for the message"
                        }
                    },
                    "required": ["message_sid"]
                }
            ),

            # Voice Call Tools
            types.Tool(
                name="twilio_make_call",
                description="Initiate a phone call using Twilio. You must provide either a TwiML URL or TwiML instructions to control what happens during the call (e.g., play message, collect input, record).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Phone number to call in E.164 format"
                        },
                        "from_": {
                            "type": "string",
                            "description": "Caller phone number (must be a Twilio phone number you own)"
                        },
                        "url": {
                            "type": "string",
                            "description": "URL that returns TwiML instructions for the call"
                        },
                        "twiml": {
                            "type": "string",
                            "description": "TwiML instructions as a string (alternative to url)"
                        },
                        "method": {
                            "type": "string",
                            "description": "HTTP method for the webhook (GET or POST, default POST)"
                        },
                        "status_callback": {
                            "type": "string",
                            "description": "URL to receive call status updates"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Seconds to wait for an answer (default 60)"
                        },
                        "record": {
                            "type": "boolean",
                            "description": "Whether to record the call (default false)"
                        }
                    },
                    "required": ["to", "from_"]
                }
            ),
            types.Tool(
                name="twilio_get_calls",
                description="Retrieve a list of calls from your Twilio account. Use this to check call history, find calls with specific status, or analyze call patterns.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of calls to retrieve (default 20, max 1000)"
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by call status",
                            "enum": ["queued", "ringing", "in-progress", "completed", "busy", "failed", "no-answer", "canceled"]
                        },
                        "from_": {
                            "type": "string",
                            "description": "Filter by caller phone number"
                        },
                        "to": {
                            "type": "string",
                            "description": "Filter by called phone number"
                        },
                        "start_time_after": {
                            "type": "string",
                            "description": "ISO date string to filter calls started after this time"
                        },
                        "start_time_before": {
                            "type": "string",
                            "description": "ISO date string to filter calls started before this time"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="twilio_get_call_by_sid",
                description="Retrieve detailed information about a specific call using its unique SID. Use this to get complete call details including duration, status, and billing information.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "call_sid": {
                            "type": "string",
                            "description": "Unique identifier (SID) for the call"
                        }
                    },
                    "required": ["call_sid"]
                }
            ),
            types.Tool(
                name="twilio_get_recordings",
                description="Retrieve call recordings from your Twilio account. Use this to access recorded conversations for quality assurance, compliance, or analysis.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of recordings to retrieve (default 20, max 1000)"
                        },
                        "call_sid": {
                            "type": "string",
                            "description": "Filter recordings by specific call SID"
                        },
                        "date_created_after": {
                            "type": "string",
                            "description": "ISO date string to filter recordings created after this date"
                        },
                        "date_created_before": {
                            "type": "string",
                            "description": "ISO date string to filter recordings created before this date"
                        }
                    },
                    "required": []
                }
            ),

            # Phone Number Management Tools
            types.Tool(
                name="twilio_search_available_numbers",
                description="Search for available phone numbers to purchase from Twilio. Use this to find numbers with specific area codes, capabilities (SMS/voice), or number patterns.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "country_code": {
                            "type": "string",
                            "description": "Two-letter country code (default 'US')",
                            "default": "US"
                        },
                        "area_code": {
                            "type": "string",
                            "description": "Specific area code to search within (e.g., '415' for San Francisco)"
                        },
                        "contains": {
                            "type": "string",
                            "description": "Search for numbers containing specific digits"
                        },
                        "sms_enabled": {
                            "type": "boolean",
                            "description": "Filter for SMS-capable numbers (default true)"
                        },
                        "voice_enabled": {
                            "type": "boolean",
                            "description": "Filter for voice-capable numbers (default true)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default 20, max 50)"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="twilio_purchase_phone_number",
                description="Purchase an available phone number from Twilio. Use this after finding a suitable number with search_available_numbers. You can configure webhooks for incoming calls and messages.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "phone_number": {
                            "type": "string",
                            "description": "Phone number to purchase in E.164 format"
                        },
                        "friendly_name": {
                            "type": "string",
                            "description": "A human-readable name for the number"
                        },
                        "voice_url": {
                            "type": "string",
                            "description": "URL to handle incoming voice calls"
                        },
                        "sms_url": {
                            "type": "string",
                            "description": "URL to handle incoming SMS messages"
                        },
                        "status_callback": {
                            "type": "string",
                            "description": "URL to receive status updates"
                        }
                    },
                    "required": ["phone_number"]
                }
            ),
            types.Tool(
                name="twilio_list_phone_numbers",
                description="List all phone numbers currently owned by your Twilio account. Use this to see your phone number inventory and their current configurations.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of numbers to retrieve (default 20, max 1000)"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="twilio_update_phone_number",
                description="Update the configuration of an existing phone number. Use this to change webhook URLs, friendly names, or other settings for numbers you own.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "phone_number_sid": {
                            "type": "string",
                            "description": "SID of the phone number to update"
                        },
                        "friendly_name": {
                            "type": "string",
                            "description": "New friendly name for the number"
                        },
                        "voice_url": {
                            "type": "string",
                            "description": "New URL to handle incoming voice calls"
                        },
                        "sms_url": {
                            "type": "string",
                            "description": "New URL to handle incoming SMS messages"
                        },
                        "status_callback": {
                            "type": "string",
                            "description": "New URL to receive status updates"
                        }
                    },
                    "required": ["phone_number_sid"]
                }
            ),
            types.Tool(
                name="twilio_release_phone_number",
                description="Release (delete) a phone number from your Twilio account. This permanently removes the number and stops all billing for it. Use with caution as this action cannot be undone.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "phone_number_sid": {
                            "type": "string",
                            "description": "SID of the phone number to release"
                        }
                    },
                    "required": ["phone_number_sid"]
                }
            ),

            # Account & Usage Tools
            types.Tool(
                name="twilio_get_account_info",
                description="Retrieve your Twilio account information including status, type, and creation date. Use this to verify account details and current status.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            types.Tool(
                name="twilio_get_balance",
                description="Get the current balance of your Twilio account. Use this to check available credit and monitor spending.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            types.Tool(
                name="twilio_get_usage_records",
                description="Retrieve usage records for your Twilio account to analyze spending patterns, track usage by category, and generate usage reports. Perfect for billing analysis and cost monitoring.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Usage category to filter by (e.g., 'sms', 'calls', 'recordings')"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date for usage period in YYYY-MM-DD format"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date for usage period in YYYY-MM-DD format"
                        },
                        "granularity": {
                            "type": "string",
                            "description": "Time granularity for the report",
                            "enum": ["daily", "monthly", "yearly", "all-time"],
                            "default": "daily"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of records to retrieve (default 50, max 1000)"
                        }
                    },
                    "required": []
                }
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        try:
            # Set authentication token in context from header or arguments
            auth_token = arguments.pop("auth_token", None)
            if auth_token:
                auth_token_context.set(auth_token)
            
            logger.info(f"Calling tool: {name} with arguments: {arguments}")

            # Route to appropriate tool function
            if name == "twilio_send_sms":
                result = await twilio_send_sms(**arguments)
            elif name == "twilio_send_mms":
                result = await twilio_send_mms(**arguments)
            elif name == "twilio_get_messages":
                result = await twilio_get_messages(**arguments)
            elif name == "twilio_get_message_by_sid":
                result = await twilio_get_message_by_sid(**arguments)
            elif name == "twilio_make_call":
                result = await twilio_make_call(**arguments)
            elif name == "twilio_get_calls":
                result = await twilio_get_calls(**arguments)
            elif name == "twilio_get_call_by_sid":
                result = await twilio_get_call_by_sid(**arguments)
            elif name == "twilio_get_recordings":
                result = await twilio_get_recordings(**arguments)
            elif name == "twilio_search_available_numbers":
                result = await twilio_search_available_numbers(**arguments)
            elif name == "twilio_purchase_phone_number":
                result = await twilio_purchase_phone_number(**arguments)
            elif name == "twilio_list_phone_numbers":
                result = await twilio_list_phone_numbers(**arguments)
            elif name == "twilio_update_phone_number":
                result = await twilio_update_phone_number(**arguments)
            elif name == "twilio_release_phone_number":
                result = await twilio_release_phone_number(**arguments)
            elif name == "twilio_get_account_info":
                result = await twilio_get_account_info(**arguments)
            elif name == "twilio_get_balance":
                result = await twilio_get_balance(**arguments)
            elif name == "twilio_get_usage_records":
                result = await twilio_get_usage_records(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            error_response = {
                "error": str(e),
                "tool": name,
                "arguments": arguments
            }
            return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]

    # Create ASGI app with both SSE and HTTP streaming
    @contextlib.asynccontextmanager
    async def create_sse_app_context(sse_transport) -> AsyncIterator[None]:
        """Context manager for the SSE server application."""
        async with sse_transport:
            yield

    @contextlib.asynccontextmanager  
    async def create_http_app_context(app) -> AsyncIterator[None]:
        """Context manager for the HTTP streaming server application."""
        yield

    async def http_handler(request):
        """Handle HTTP requests for MCP server."""
        from starlette.responses import JSONResponse
        import json
        
        # Simple health check for GET requests
        if request.method == "GET":
            return JSONResponse({
                "server": "twilio-mcp-server", 
                "status": "running",
                "endpoints": {
                    "sse": "/sse",
                    "http": "/"
                }
            })
        
        # Handle POST requests (MCP tool calls)
        if request.method == "POST":
            try:
                body = await request.body()
                if not body:
                    return JSONResponse({"error": "Empty request body"}, status_code=400)
                
                # Parse JSON request
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    return JSONResponse({"error": "Invalid JSON"}, status_code=400)
                
                # Extract tool call information
                method = data.get("method")
                params = data.get("params", {})
                
                if method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    # Set auth token if provided
                    auth_token = arguments.pop("auth_token", None)
                    if auth_token:
                        auth_token_context.set(auth_token)
                    
                    # Call the appropriate tool
                    logger.info(f"Calling tool: {tool_name} with arguments: {arguments}")
                    
                    try:
                        # Route to appropriate tool function (same logic as in call_tool)
                        # Messaging tools
                        if tool_name == "twilio_send_sms":
                            from tools import twilio_send_sms
                            result = await twilio_send_sms(**arguments)
                        elif tool_name == "twilio_send_mms":
                            from tools import twilio_send_mms
                            result = await twilio_send_mms(**arguments)
                        elif tool_name == "twilio_get_messages":
                            from tools import twilio_get_messages
                            result = await twilio_get_messages(**arguments)
                        elif tool_name == "twilio_get_message_by_sid":
                            from tools import twilio_get_message_by_sid
                            result = await twilio_get_message_by_sid(**arguments)
                        # Voice tools
                        elif tool_name == "twilio_make_call":
                            from tools import twilio_make_call
                            result = await twilio_make_call(**arguments)
                        elif tool_name == "twilio_get_calls":
                            from tools import twilio_get_calls
                            result = await twilio_get_calls(**arguments)
                        elif tool_name == "twilio_get_call_by_sid":
                            from tools import twilio_get_call_by_sid
                            result = await twilio_get_call_by_sid(**arguments)
                        elif tool_name == "twilio_get_recordings":
                            from tools import twilio_get_recordings
                            result = await twilio_get_recordings(**arguments)
                        # Phone number tools
                        elif tool_name == "twilio_search_available_numbers":
                            from tools import twilio_search_available_numbers
                            result = await twilio_search_available_numbers(**arguments)
                        elif tool_name == "twilio_purchase_phone_number":
                            from tools import twilio_purchase_phone_number
                            result = await twilio_purchase_phone_number(**arguments)
                        elif tool_name == "twilio_list_phone_numbers":
                            from tools import twilio_list_phone_numbers
                            result = await twilio_list_phone_numbers(**arguments)
                        elif tool_name == "twilio_update_phone_number":
                            from tools import twilio_update_phone_number
                            result = await twilio_update_phone_number(**arguments)
                        elif tool_name == "twilio_release_phone_number":
                            from tools import twilio_release_phone_number
                            result = await twilio_release_phone_number(**arguments)
                        # Account tools
                        elif tool_name == "twilio_get_account_info":
                            from tools import twilio_get_account_info
                            result = await twilio_get_account_info(**arguments)
                        elif tool_name == "twilio_get_balance":
                            from tools import twilio_get_balance
                            result = await twilio_get_balance(**arguments)
                        elif tool_name == "twilio_get_usage_records":
                            from tools import twilio_get_usage_records
                            result = await twilio_get_usage_records(**arguments)
                        else:
                            return JSONResponse({"error": f"Unknown tool: {tool_name}"}, status_code=400)
                        
                        return JSONResponse({"result": result})
                        
                    except Exception as e:
                        logger.error(f"Error calling tool {tool_name}: {e}")
                        return JSONResponse({"error": str(e)}, status_code=500)
                
                elif method == "tools/list":
                    # Return list of available tools
                    tools = await app.handlers.get(types.ListToolsRequest)()
                    tool_list = [{"name": tool.name, "description": tool.description} for tool in tools]
                    return JSONResponse({"tools": tool_list})
                
                else:
                    return JSONResponse({"error": f"Unknown method: {method}"}, status_code=400)
                    
            except Exception as e:
                logger.error(f"Error handling request: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)
        
        return JSONResponse({"error": "Method not allowed"}, status_code=405)

    # Create SSE transport for real-time streaming
    sse_transport = SseServerTransport("/sse")

    # Mount both endpoints
    routes = [
        Mount("/sse", sse_transport, name="sse"),
        Route("/{path:path}", http_handler, methods=["GET", "POST"]),
    ]

    starlette_app = Starlette(
        routes=routes,
        lifespan=create_http_app_context,
    )

    # Run the server
    import uvicorn
    logger.info(f"Starting Twilio MCP Server on port {port}")
    logger.info("Available endpoints:")
    logger.info(f"  - SSE: http://localhost:{port}/sse")
    logger.info(f"  - HTTP: http://localhost:{port}/")
    
    uvicorn.run(starlette_app, host="0.0.0.0", port=port, log_level=log_level.lower())
    
    return 0

if __name__ == "__main__":
    exit(main())
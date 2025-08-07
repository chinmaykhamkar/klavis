# Twilio MCP Server

A comprehensive Model Context Protocol (MCP) server implementation that provides full integration with Twilio's communication APIs. This server enables AI agents to send SMS/MMS messages, make voice calls, manage phone numbers, and monitor account usage through a set of atomic, well-designed tools.

## Features

- **=� SMS & MMS Messaging**: Send text messages and multimedia content
- **=� Voice Calls**: Initiate calls with TwiML control and call management  
- **=" Phone Number Management**: Search, purchase, configure, and release phone numbers
- **=� Account Monitoring**: Check balances, usage records, and account information
- **= Dual Transport Support**: SSE and Streamable HTTP endpoints
- **= Secure Authentication**: Context-aware token management with environment fallback
- **=� Detailed Logging**: Configurable logging with rich operational context
- **� Error Handling**: Comprehensive error handling with actionable error messages

## Tools Overview

The server provides 15 atomic tools organized into four main categories:

### =� Messaging Operations
- `twilio_send_sms`: Send SMS messages with delivery tracking
- `twilio_send_mms`: Send multimedia messages with up to 10 attachments
- `twilio_get_messages`: Retrieve message history with flexible filtering
- `twilio_get_message_by_sid`: Get detailed information about specific messages

### =� Voice Operations  
- `twilio_make_call`: Initiate phone calls with TwiML instructions
- `twilio_get_calls`: Retrieve call history with status filtering
- `twilio_get_call_by_sid`: Get detailed call information including duration and costs
- `twilio_get_recordings`: Access call recordings for analysis

### =" Phone Number Management
- `twilio_search_available_numbers`: Find available numbers by area code or pattern
- `twilio_purchase_phone_number`: Purchase numbers with webhook configuration
- `twilio_list_phone_numbers`: View all owned phone numbers and their settings
- `twilio_update_phone_number`: Modify number configurations and webhooks
- `twilio_release_phone_number`: Release numbers to stop billing

### =� Account & Usage Monitoring
- `twilio_get_account_info`: Retrieve account details and status
- `twilio_get_balance`: Check current account balance
- `twilio_get_usage_records`: Generate detailed usage reports by category and time period

## Installation & Setup

### Prerequisites

1. **Twilio Account**: Sign up at [twilio.com](https://www.twilio.com)
2. **API Credentials**: Obtain your Account SID and Auth Token from the Twilio Console
3. **Python 3.8+**: Required for running the server
4. **Phone Number**: Purchase at least one Twilio phone number for sending messages/calls

### Quick Setup Guide

#### Step 1: Get Twilio Credentials
1. Sign up or log in to [Twilio Console](https://console.twilio.com)
2. Navigate to **Account Dashboard**
3. Copy your **Account SID** and **Auth Token**
4. (Optional) Purchase a phone number from **Phone Numbers > Manage > Buy a number**

#### Step 2: Configure Environment Variables
1. **Copy the example environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your actual Twilio credentials:

### Local Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify your setup**:
   ```bash
   # Check that your .env file exists and has the right variables
   cat .env
   ```

3. **Run the server**:
   ```bash
   python server.py
   ```

4. **Verify the server is running**:
   - You should see logs indicating the server started successfully
   - The server will be available at `http://localhost:5000`

3. **Custom configuration**:
   ```bash
   # Custom port and logging level
   python server.py --port 8080 --log-level DEBUG
   
   # Enable JSON responses instead of SSE streams  
   python server.py --json-response
   ```

### Docker Installation (Recommended)

1. **Set up environment variables** (same as local setup):
   ```bash
   cp .env.example .env
   # Edit .env with your Twilio credentials
   ```

2. **Build the Docker image**:
   ```bash
   docker build -t klavis-twilio .
   ```

3. **Run with environment file** (easiest method):
   ```bash
   docker run -p 5000:5000 --env-file .env klavis-twilio
   ```

4. **Alternative: Run with individual environment variables**:
   ```bash
   docker run -p 5000:5000 \
     -e TWILIO_ACCOUNT_SID=your_account_sid \
     -e TWILIO_AUTH_TOKEN=your_auth_token \
     klavis-twilio
   ```

## Usage Examples

### Connecting with MCP Clients

The server provides two endpoints for different use cases:

- **SSE Endpoint**: `http://localhost:5000/sse` (real-time streaming)
- **HTTP Endpoint**: `http://localhost:5000/` (request-response)

### Example Tool Calls

#### Send an SMS Message
```json
{
  "tool": "twilio_send_sms",
  "arguments": {
    "to": "+1234567890",
    "from_": "+1987654321", 
    "body": "Hello from Twilio MCP Server! =�"
  }
}
```

#### Make a Voice Call
```json
{
  "tool": "twilio_make_call",
  "arguments": {
    "to": "+1234567890",
    "from_": "+1987654321",
    "twiml": "<Response><Say>Hello, this is a test call from Twilio!</Say></Response>"
  }
}
```

#### Search for Available Numbers
```json
{
  "tool": "twilio_search_available_numbers", 
  "arguments": {
    "country_code": "US",
    "area_code": "415",
    "sms_enabled": true,
    "voice_enabled": true,
    "limit": 10
  }
}
```

#### Check Account Usage
```json
{
  "tool": "twilio_get_usage_records",
  "arguments": {
    "category": "sms",
    "granularity": "daily",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }
}
```

## Configuration & Webhooks

### Setting Up Webhooks

Many Twilio features require webhook URLs for real-time notifications:

- **SMS Status Updates**: Get delivery confirmations
- **Call Status Updates**: Track call progress and completion
- **Incoming Messages**: Handle replies and conversations
- **Incoming Calls**: Control call flow with TwiML

Example webhook configuration when purchasing a number:
```json
{
  "tool": "twilio_purchase_phone_number",
  "arguments": {
    "phone_number": "+1234567890",
    "friendly_name": "Customer Service Line",
    "voice_url": "https://your-domain.com/voice-webhook",
    "sms_url": "https://your-domain.com/sms-webhook"
  }
}
```

### TwiML for Voice Calls

TwiML (Twilio Markup Language) controls call behavior. Common examples:

**Simple Message**:
```xml
<Response>
  <Say>Thank you for calling! Your call is important to us.</Say>
</Response>
```

**Interactive Menu**:
```xml
<Response>
  <Gather numDigits="1" action="/handle-choice">
    <Say>Press 1 for Sales, Press 2 for Support</Say>
  </Gather>
</Response>
```

**Record a Message**:
```xml
<Response>
  <Say>Please leave your message after the beep.</Say>
  <Record maxLength="60" action="/handle-recording"/>
</Response>
```

## Error Handling & Troubleshooting

The server provides detailed error information to help diagnose issues:

### Common Error Scenarios

1. **Authentication Errors**:
   - Verify `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` are correct
   - Check that credentials haven't expired or been rotated

2. **Phone Number Format Errors**:
   - Ensure numbers are in E.164 format (e.g., `+1234567890`)
   - US numbers: 11 digits total including country code

3. **Permission Errors**:
   - Verify your Twilio account has sufficient permissions
   - Check if services (SMS, Voice) are enabled in your region

4. **Rate Limiting**:
   - Twilio has rate limits on API calls and messaging
   - Implement exponential backoff for production use

5. **Webhook Delivery**:
   - Ensure webhook URLs are publicly accessible
   - Use HTTPS endpoints for production
   - Verify webhook endpoints return HTTP 200 status

### Debugging Tips

1. **Enable Debug Logging**:
   ```bash
   python server.py --log-level DEBUG
   ```

2. **Test with Twilio Console**: 
   - Use Twilio's REST API Explorer to test credentials
   - Send test messages through the Console first

3. **Webhook Testing**:
   - Use tools like ngrok for local webhook testing
   - Check webhook logs in Twilio Console

## API Rate Limits & Best Practices

### Twilio Rate Limits
- **REST API**: 100 requests per second (default)
- **SMS Messages**: Varies by account type and phone number
- **Voice Calls**: Concurrent call limits apply

### Best Practices

1. **Authentication**:
   - Store credentials securely using environment variables
   - Rotate Auth Tokens periodically
   - Use subaccounts for organization

2. **Phone Number Management**:
   - Purchase numbers in advance for high-volume use
   - Configure appropriate webhook URLs
   - Monitor number usage and costs

3. **Message Delivery**:
   - Implement status callbacks for delivery confirmation
   - Handle failed messages gracefully
   - Respect opt-out requests

4. **Cost Optimization**:
   - Monitor usage records regularly
   - Set up usage alerts and triggers
   - Choose appropriate phone number types for your use case

## Security Considerations

1. **Credential Security**:
   - Never commit credentials to version control
   - Use environment variables or secure secret management
   - Implement proper access controls

2. **Webhook Security**:
   - Validate webhook signatures from Twilio
   - Use HTTPS endpoints in production
   - Implement proper request validation

3. **Data Privacy**:
   - Handle phone numbers and message content according to regulations
   - Implement proper data retention policies
   - Respect user privacy preferences

## Development & Testing

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt pytest pytest-asyncio

# Run tests
pytest tests/ -v
```

### Local Development

1. **Set up development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Use Twilio Test Credentials**:
   - Use Twilio's test credentials for development
   - Test credentials don't send real messages or make real calls

3. **Webhook Development**:
   - Use ngrok or similar tools to expose local webhooks
   - Test webhook flows thoroughly

### Quick Start Commands

To get the server running quickly:

```bash
# 1. Navigate to the twilio directory
cd mcp_servers/twilio

# 2. Set up your environment
cp .env.example .env
# Edit .env with your actual Twilio credentials

# 3. Install and run
pip install -r requirements.txt
python server.py --log-level DEBUG

# Server will be available at http://localhost:5000
```

Or with Docker:
```bash
# 1. Set up environment and build
cp .env.example .env
# Edit .env with your actual Twilio credentials  
docker build -t klavis-twilio .

# 2. Run the server
docker run -p 5000:5000 --env-file .env klavis-twilio
```

## Contributing

We welcome contributions! Please see the main [Contributing Guide](../../CONTRIBUTING.md) for details on:

- Code style guidelines
- Pull request process  
- Testing requirements
- Documentation standards

### Twilio-Specific Contribution Guidelines

- Test all tools with both valid and invalid inputs
- Ensure proper error handling for Twilio API errors
- Update documentation for any new Twilio features
- Include usage examples for new tools

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Support & Resources

- **Twilio Documentation**: [https://www.twilio.com/docs](https://www.twilio.com/docs)
- **Twilio Console**: [https://console.twilio.com](https://console.twilio.com)
- **MCP Specification**: [https://modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Issues**: [Report bugs or request features](https://github.com/klavis-ai/klavis/issues)

---

Built with d for the Klavis AI ecosystem. This server provides a comprehensive bridge between AI agents and Twilio's powerful communication platform, enabling rich conversational experiences and automated communication workflows.
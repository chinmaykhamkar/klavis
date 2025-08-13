# Moneybird MCP Server

An MCP (Model Context Protocol) server that provides integration with [Moneybird](https://moneybird.com) through their REST API v2.

## Features

This MCP server provides tools to interact with Moneybird, including:

### Administration (1 tool)
- **moneybird_list_administrations**: List all administrations the authenticated user has access to (call this first!)

### Contacts (3 tools)
- **moneybird_list_contacts**: List all contacts with optional search filtering
- **moneybird_get_contact**: Get details for a specific contact by ID
- **moneybird_create_contact**: Create new contacts with company or person information

### Sales & Invoicing (3 tools)
- **moneybird_list_sales_invoices**: List all sales invoices with filtering options (state, period, contact, dates)
- **moneybird_get_sales_invoice**: Get details for a specific sales invoice by ID
- **moneybird_create_sales_invoice**: Create new sales invoices with line items and contact information

### Financial Management (2 tools)
- **moneybird_list_financial_accounts**: List all financial accounts in the administration
- **moneybird_list_products**: List all products with optional search filtering

### Project & Time Management (2 tools)
- **moneybird_list_projects**: List all projects with optional state filtering (active, archived, all)
- **moneybird_list_time_entries**: List all time entries with filtering by period, contact, project, or user

## Setup

### Prerequisites
- Python 3.12 or higher
- A Moneybird account with API access
- Moneybird API token (Bearer token for API authentication)
- Moneybird Administration ID (found in your Moneybird account settings)

### Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your actual values
nano .env
```

3. Configure your `.env` file:
```bash
# Required: Your Moneybird API token
MONEYBIRD_API_TOKEN=your_actual_moneybird_api_token_here

# Optional: Server port (defaults to 5000)
MONEYBIRD_MCP_SERVER_PORT=5000
```

4. Run the server:
```bash
python server.py
```

### Docker Setup

1. Build the Docker image:
```bash
docker build -f mcp_servers/moneybird/Dockerfile -t moneybird-mcp-server .
```

2. Run the container:
```bash
docker run -p 5000:5000 moneybird-mcp-server
```

## Authentication

The server supports two authentication methods:

### Method 1: HTTP Header (Recommended for API calls)
Provide the API token in the `x-auth-token` header:
```
x-auth-token: your_moneybird_api_token_here
```

### Method 2: Environment Variable (Great for local testing)
Set the token in your `.env` file:
```bash
MONEYBIRD_API_TOKEN=your_moneybird_api_token_here
```

**Priority**: HTTP header takes precedence over environment variable. This allows you to:
- Use `.env` for local development/testing
- Override with headers for production API calls

## API Endpoints

The server provides endpoints for both transport methods:

- `/sse` - Server-Sent Events endpoint for real-time communication
- `/messages/` - SSE message handling endpoint
- `/mcp` - StreamableHTTP endpoint for direct API calls

## Tool Usage Examples

### Get Available Administrations (Start Here!)
```json
{
  "name": "moneybird_list_administrations",
  "arguments": {}
}
```

### List All Contacts
```json
{
  "name": "moneybird_list_contacts",
  "arguments": {
    "administration_id": "123456789",
    "query": "john@example.com"
  }
}
```

### Get a Specific Contact
```json
{
  "name": "moneybird_get_contact",
  "arguments": {
    "administration_id": "123456789",
    "contact_id": "987654321"
  }
}
```

### Create a New Contact
```json
{
  "name": "moneybird_create_contact",
  "arguments": {
    "administration_id": "123456789",
    "contact_data": {
      "contact": {
        "company_name": "Acme Corp",
        "email": "info@acme.com",
        "phone": "+1234567890"
      }
    }
  }
}
```

### List Sales Invoices with Filters
```json
{
  "name": "moneybird_list_sales_invoices",
  "arguments": {
    "administration_id": "123456789",
    "state": "open",
    "period": "this_month"
  }
}
```

### Get a Specific Sales Invoice
```json
{
  "name": "moneybird_get_sales_invoice",
  "arguments": {
    "administration_id": "123456789",
    "invoice_id": "456789123"
  }
}
```

### Create a Sales Invoice
```json
{
  "name": "moneybird_create_sales_invoice",
  "arguments": {
    "administration_id": "123456789",
    "invoice_data": {
      "sales_invoice": {
        "contact_id": "987654321",
        "invoice_date": "2024-01-15",
        "due_date": "2024-02-15",
        "reference": "INV-001",
        "details_attributes": [
          {
            "description": "Consulting services",
            "price": "100.00",
            "amount": "10"
          }
        ]
      }
    }
  }
}
```

### List Financial Accounts
```json
{
  "name": "moneybird_list_financial_accounts",
  "arguments": {
    "administration_id": "123456789"
  }
}
```

### List Products
```json
{
  "name": "moneybird_list_products",
  "arguments": {
    "administration_id": "123456789",
    "query": "consulting"
  }
}
```

### List Projects
```json
{
  "name": "moneybird_list_projects",
  "arguments": {
    "administration_id": "123456789",
    "state": "active"
  }
}
```

### List Time Entries
```json
{
  "name": "moneybird_list_time_entries",
  "arguments": {
    "administration_id": "123456789",
    "period": "this_week",
    "project_id": "555666777"
  }
}
```

## Testing the Server

### Local Testing with curl

1. **Start the server:**
```bash
python server.py
```

2. **Test the SSE endpoint:**
```bash
curl -H "x-auth-token: YOUR_MONEYBIRD_API_TOKEN" \
     -H "Content-Type: application/json" \
     http://localhost:5000/sse
```

3. **Test a tool call via StreamableHTTP:**
```bash
curl -X POST \
     -H "x-auth-token: YOUR_MONEYBIRD_API_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "method": "tools/call",
       "params": {
         "name": "moneybird_list_contacts",
         "arguments": {
           "administration_id": "YOUR_ADMINISTRATION_ID"
         }
       }
     }' \
     http://localhost:5000/mcp
```

### Testing with Python

```python
import httpx
import json

# Configuration
API_TOKEN = "your_moneybird_api_token"
SERVER_URL = "http://localhost:5000"

async def test_moneybird_tools():
    headers = {
        "x-auth-token": API_TOKEN,
        "Content-Type": "application/json"
    }
    
    # First, get available administrations
    admin_payload = {
        "method": "tools/call",
        "params": {
            "name": "moneybird_list_administrations",
            "arguments": {}
        }
    }
    
    async with httpx.AsyncClient() as client:
        # Get administrations
        admin_response = await client.post(f"{SERVER_URL}/mcp", 
                                         headers=headers, 
                                         json=admin_payload)
        print("Administrations:", admin_response.json())
        
        # Extract first administration ID from response
        # (adjust based on actual API response structure)
        admin_data = admin_response.json()
        if admin_data and len(admin_data) > 0:
            administration_id = str(admin_data[0]["id"])
            
            # Test listing contacts with the administration ID
            contacts_payload = {
                "method": "tools/call",
                "params": {
                    "name": "moneybird_list_contacts",
                    "arguments": {
                        "administration_id": administration_id
                    }
                }
            }
            
            contacts_response = await client.post(f"{SERVER_URL}/mcp", 
                                               headers=headers, 
                                               json=contacts_payload)
            print("Contacts response:", contacts_response.json())

# Run the test
import asyncio
asyncio.run(test_moneybird_tools())
```

## Recommended Workflow

1. **Start with Administration Discovery**:
   ```bash
   # First call to discover available administrations
   moneybird_list_administrations
   ```

2. **Select Administration**: From the response, note the `id` of the administration you want to work with

3. **Use Other Tools**: Pass the selected `administration_id` to all subsequent tool calls

**Example LLM Conversation Flow**:
```
User: "Show me my Moneybird contacts"
LLM: "Let me first get your available administrations..."
     → Calls moneybird_list_administrations
LLM: "I found these administrations: [Company A (id: 123), Company B (id: 456)]. 
     Which one would you like to work with?"
User: "Company A"
LLM: → Calls moneybird_list_contacts with administration_id: "123"
```

## Getting Your Moneybird Credentials

### API Token
1. Log into your Moneybird account
2. Go to Settings > Account Settings
3. Navigate to the "API" or "Integrations" section
4. Generate a new API token
5. Copy the token for use in the `x-auth-token` header

### Administration ID
1. In your Moneybird account, the administration ID is visible in the URL
2. Look for a URL like: `https://moneybird.com/123456789/dashboard`
3. The number `123456789` is your administration ID

## Error Handling

The server provides detailed error messages for common issues:
- Missing required parameters (administration_id, contact_id, etc.)
- Authentication failures (invalid or missing API token)
- API rate limiting (Moneybird allows 150 requests per 5 minutes)
- Invalid administration IDs
- Network connectivity issues

## Rate Limiting

Moneybird API has rate limits of 150 requests per 5 minutes. The server will handle rate limit responses appropriately. See the [Moneybird API documentation](https://developer.moneybird.com/) for current limits.

## Contributing

1. Follow the existing code structure
2. Add new tools to the appropriate files in the `tools/` directory
3. Update `tools/__init__.py` to export new functions
4. Add tool definitions to `server.py`
5. Update this README with new functionality

## License

This project follows the same license as the parent Klavis project.
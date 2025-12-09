# Otto - CFO Financial Planning MCP Server

A Model Context Protocol (MCP) server providing financial planning and analysis tools for CFOs.

## Features

- Financial burn rate analysis by function
- Runway calculations with CapEx delay scenarios
- Variance reporting (actual vs budget)
- OAuth 2.0 authentication with Google (optional)

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL database
- Google OAuth credentials (if authentication is enabled)

### Installation

```bash
# Install dependencies
uv sync --all-extras --all-packages --group dev
```

### Configuration

Create a `.env` file with the following settings:

```bash
# Server Configuration
HOST=localhost
PORT=8000
SERVER_URL=http://localhost:8000

# PostgreSQL Configuration
POSTGRES__URL=postgresql://user:password@localhost:5432/dbname
POSTGRES__SCHEMA_NAME=public

# Google OAuth Configuration (optional)
GOOGLE_OAUTH__CLIENT_ID=your-client-id
GOOGLE_OAUTH__CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH__ENABLE_AUTH=false  # Set to true to enable authentication
GOOGLE_OAUTH__CALLBACK_PATH=http://localhost:8000/cfo/callback
```

## Authentication

### Disabling Authentication (Development)

For local development and testing, you can disable authentication:

```bash
GOOGLE_OAUTH__ENABLE_AUTH=false
```

### Enabling Google OAuth

1. Create OAuth 2.0 credentials in [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Add authorized redirect URI: `http://localhost:8000/cfo/auth/callback`
3. Set environment variables:
   ```bash
   GOOGLE_OAUTH__ENABLE_AUTH=true
   GOOGLE_OAUTH__CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_OAUTH__CLIENT_SECRET=your-client-secret
   ```

### OAuth Discovery Endpoints

The server implements OAuth 2.0 discovery endpoints:

- `/.well-known/oauth-authorization-server` - Authorization server metadata
- `/.well-known/oauth-protected-resource` - Protected resource metadata

## Running the Server

```bash
# Using UV
uv run -m otto.cli run

# Or directly with Python
python -m otto.cli run
```

The server will be available at `http://localhost:8000/cfo/mcp`

## Available Tools

### UserInfo

Get information about the authenticated user (requires authentication).

### Datasets

Get the list of available datasets with sample data.

### BurnByFunction

Calculate burn rate broken down by business function.

### Runway

Calculate runway based on burn rate and cash balance, with optional CapEx delay.

**Parameters:**

- `delay_capex_days` (int): Number of days to delay CapEx payments

### VarianceReport

Generate actual vs budget variance report.

**Parameters:**

- `fiscal_quarter` (str): Fiscal quarter (e.g., "Q1", "Q2", "Q3", "Q4")
- `budget_version` (str): Budget version (e.g., "BUDGET_2024")

## Development

### Running Tests

```bash
uv run pytest
```

### Linting and Formatting

```bash
# Format code
uv run ruff format && uv run ruff check --fix

# Run linter
uv run ruff check

# Type checking
uv run mypy .
```

### Coverage

```bash
uv run coverage run -m pytest && uv run coverage xml -o coverage.xml && uv run coverage report -m --fail-under=95
```

## Troubleshooting

### 401 Unauthorized Errors

If you're seeing `Auth error returned: invalid_token (status=401)`:

1. Check if authentication is needed for your use case
2. To disable authentication, set `GOOGLE_OAUTH__ENABLE_AUTH=false` in your `.env` file
3. If authentication is needed, ensure your OAuth credentials are valid and the redirect URI is configured correctly in Google Cloud Console

### 404 Errors on OAuth Endpoints

The OAuth discovery endpoints are now implemented at:

- `/.well-known/oauth-authorization-server`
- `/.well-known/oauth-protected-resource`

Make sure your MCP client is configured to use `http://localhost:8000/cfo/mcp` as the server URL.

## License

[Add your license here]

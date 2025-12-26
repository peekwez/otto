import contextlib
from collections.abc import AsyncGenerator
from typing import Any

import pandas as pd
from cryptography.fernet import Fernet
from fastmcp import Context, FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider
from fastmcp.server.dependencies import AccessToken, get_access_token
from key_value.aio.stores.redis import RedisStore
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
from starlette.exceptions import HTTPException

from otto.core.logging import get_logger
from otto.core.settings import get_settings
from otto.tools.analytics.burn import burn_by_function
from otto.tools.analytics.runway import calculate_runway
from otto.tools.analytics.variance import variance_report
from otto.tools.analytics.income_statement import income_statement
from otto.tools.utils import load_all_tables

_dfs: dict[str, pd.DataFrame] = {}


def load_datasets() -> None:
    global _dfs
    logger = get_logger(__name__)
    _dfs = load_all_tables()
    logger.info("Loaded all tables for MCP.")


@contextlib.asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncGenerator[None, None]:
    async with contextlib.AsyncExitStack() as _:
        load_datasets()
        yield


def create_server() -> FastMCP:
    settings = get_settings()
    logger = get_logger(__name__)

    auth_provider = None
    if settings.google_oauth.enable_auth:
        logger.info("Authentication is ENABLED - OAuth required for MCP endpoints")
        scopes = settings.google_oauth.scopes.split(",")
        kwargs: dict[str, Any] = {}
        if settings.stage == "prod":
            if not settings.redis.host:
                raise ValueError(
                    "Redis host must be set in production for token storage."
                )
            client_storage = FernetEncryptionWrapper(
                key_value=RedisStore(
                    host=settings.redis.host.host,  # type: ignore
                    port=settings.redis.port,
                ),
                fernet=Fernet(settings.keys.storage_encryption_key.get_secret_value()),
            )
            kwargs = {
                "jwt_signing_key": settings.keys.jwt_signing_key.get_secret_value(),
                "client_storage": client_storage,
            }
        auth_provider = GoogleProvider(
            client_id=settings.google_oauth.client_id,
            client_secret=settings.google_oauth.client_secret.get_secret_value(),
            base_url=settings.server_url,
            issuer_url=settings.server_url,
            required_scopes=scopes,
            redirect_path=settings.google_oauth.callback_path,
            **kwargs,
        )

        # Production token management

    else:
        logger.info(
            "Authentication is DISABLED - MCP endpoints accessible without OAuth"
        )

    app = FastMCP(
        name="CFO Financial Planning MCP",
        instructions="A financial planning and analysis tools for CFOs.",
        auth=auth_provider,
        lifespan=lifespan,
        website_url=settings.server_url.encoded_string(),
    )

    # Add a protected tool to test authentication
    @app.tool(
        name="GetUserInfo", description="Get information about the authenticated user"
    )
    async def get_user_info() -> dict[str, Any]:  # type: ignore
        """Returns information about the authenticated Google user."""

        token: AccessToken | None = get_access_token()
        if token is None:
            raise HTTPException(401, "Unauthorized")

        # The GoogleProvider stores user data in token claims
        return {
            "google_id": token.claims.get("sub"),
            "email": token.claims.get("email"),
            "name": token.claims.get("name"),
            "picture": token.claims.get("picture"),
            "locale": token.claims.get("locale"),
        }

    @app.tool(
        name="Datasets",
        description="Get the list of available datasets",
    )
    def get_datasets_tool(ctx: Context) -> dict[str, str]:  # type: ignore
        """
        Get the list of available datasets.

        Args:
            ctx (Context): MCP context

        Returns:
            dict[str, str]: Dictionary with dataset names and their markdown
                representations
        """
        return {key: df.head().to_markdown() for key, df in _dfs.items()}

    @app.tool(
        name="BurnByFunction",
        description="Calculate burn by function",
    )
    def burn_by_function_tool(ctx: Context) -> dict[str, Any]:  # type: ignore
        result = burn_by_function(_dfs)
        return result

    @app.tool(
        name="Runway",
        description="Calculate runway based on burn rate and cash balance",
    )
    def runway_tool(delay_capex_days: int, ctx: Context) -> dict[str, Any]:  # type: ignore
        """
        Calculate runway based on burn rate and cash balance.

        Args:
            delay_capex_days (int): Number of days to delay CapEx payments
            ctx (Context): MCP context

        Returns:
            dict[str, Any]: Dictionary with runway information
        """
        result = calculate_runway(_dfs, delay_capex_days=delay_capex_days)
        return result

    @app.tool(
        name="VarianceReport",
        description="Generate actual vs budget variance report by fiscal "
        "quarter and budget version",
    )
    def variance_report_tool(  # type: ignore
        fiscal_quarter: str,
        budget_version: str,
        ctx: Context,  # type: ignore
    ) -> dict[str, Any]:
        """
        Generate actual vs budget variance report by fiscal quarter and budget version.

        Args:
            fiscal_quarter (str): Fiscal quarter (e.g., "Q1", "Q2")
            budget_version (str): Budget version (e.g., "BUDGET_2024")
            ctx (Context): MCP context

        Returns:
            dict[str, Any]: Dictionary with variance report information
        """
        result = variance_report(_dfs, fiscal_quarter, budget_version)
        return result

    @app.tool(
        name="IncomeStatement",
        description="Generate income statement report",
    )
    def income_statement_tool(ctx: Context) -> dict[str, Any]:  # type: ignore
        """
        Generate income statement report using Couqley Data.

        Args:
            ctx (Context): MCP context

        Returns:
            dict[str, Any]: Dictionary with income statement report information
        """
        result = income_statement(_dfs)
        return result

    return app


def run_app(host: str, port: int) -> None:
    from otto.app.tunnel import start_ngrok, stop_ngrok
    from otto.core.logging import patch_server_logging

    _logger = get_logger(__name__)
    settings = get_settings()

    patch_server_logging(_logger)

    if settings.ngrok.enable_tunnel:
        url = start_ngrok(f"{port}")
        _logger.info(f"ngrok tunnel started at {url}")

    try:
        mcp: FastMCP = create_server()
        mcp.run(
            transport="streamable-http",
            host=host,
            port=port,
            uvicorn_config={"log_level": "info", "log_config": None},
        )
    except Exception as e:
        _logger.error(f"Error running MCP server: {e}")
    finally:
        _logger.info("Shutting down ngrok tunnel...")
        if settings.ngrok.enable_tunnel:
            stop_ngrok()

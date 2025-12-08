from typing import Any

# import httpx
import pandas as pd

# from mcp.server.auth.middleware.auth_context import get_access_token
# from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
# from mcp.server.fastmcp import Context, FastMCP
from fastmcp import Context, FastMCP
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from otto.app.google_auth import GoogleOAuthProvider
from otto.core.logging import get_logger
from otto.tools.analytics.burn import burn_by_function
from otto.tools.analytics.runway import calculate_runway
from otto.tools.analytics.variance import variance_report
from otto.tools.utils import load_all_tables

_dfs: dict[str, pd.DataFrame] = {}


def load_datasets() -> None:
    global _dfs
    logger = get_logger(__name__)
    _dfs = load_all_tables()
    logger.info("Loaded all tables for MCP.")


def create_server() -> FastMCP:
    logger = get_logger(__name__)
    # settings = get_settings()
    oauth_provider = GoogleOAuthProvider()

    # auth_settings = AuthSettings(
    #     issuer_url=settings.server_url,
    #     client_registration_options=ClientRegistrationOptions(
    #         enabled=True,
    #         valid_scopes=settings.google_oauth.scope.split(),
    #         default_scopes=settings.google_oauth.scope.split(),
    #     ),
    #     resource_server_url=settings.server_url,
    #     required_scopes=["openid"],
    # )

    app = FastMCP(
        name="cfo_mcp",
        instructions="A financial planning and analysis tools for CFOs.",
    )

    @app.custom_route("/callback", methods=["GET"])
    async def callback_handler(request: Request) -> Response:  # type: ignore
        """Handle Google OAuth callback."""
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code or not state:
            raise HTTPException(400, "Missing code or state parameter")

        try:
            redirect_uri = await oauth_provider.handle_callback(code, state)
            return RedirectResponse(status_code=302, url=redirect_uri)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error", exc_info=e)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "server_error",
                    "error_description": "Unexpected error",
                },
            )

    # def get_token() -> str:
    #     """Get the ADP token for the authenticated user."""
    #     access_token = get_access_token()
    #     if not access_token:
    #         raise ValueError("Not authenticated")

    #     # Get ADP token from mapping
    #     adp_token = oauth_provider.token_mapping.get(access_token.token)

    #     if not adp_token:
    #         raise ValueError("No ADP token found for user")

    #     return adp_token

    # @app.tool(
    #     name="GetGoogleProfile",
    #     description="Get the authenticated user's Google profile information",
    # )
    # async def get_google_profile() -> dict[str, Any]:  # type: ignore
    #     """Get the authenticated user's profile information.

    #     This is the only tool in our example.
    #     """
    #     google_token = get_token()

    #     # make a request to Google API to get user profile using httpx
    #     user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    #     async with httpx.AsyncClient() as client:
    #         response = await client.get(
    #             user_info_url, headers={"Authorization": f"Bearer {google_token}"}
    #         )
    #         if response.status_code != 200:
    #             raise HTTPException(
    #                 status_code=response.status_code,
    #                 detail="Failed to fetch user profile",
    #             )
    #         return response.json()

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

    return app


mcp: FastMCP = create_server()
mcp_app = mcp.http_app(path="/mcp", transport="streamable-http")

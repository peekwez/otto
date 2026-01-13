from typing import Any

from fastmcp import Client

from otto.core.logging import get_logger


async def connect() -> None:
    # The client will automatically handle Google OAuth
    logger = get_logger(__name__)
    async with Client("https://api.docex.io/mcp", auth="oauth") as client:
        # First-time connection will open Google login in your browser
        logger.info("✓ Authenticated with Google!")

        # Test the protected tool
        result: Any = await client.call_tool("GetUserInfo")  # type: ignore
        logger.info(f"Tool call result: {result}")

import asyncio
from typing import Any

from fastmcp import Client


async def main() -> None:
    # The client will automatically handle Google OAuth
    async with Client("http://localhost:8000/cfo/mcp", auth="oauth") as client:
        # First-time connection will open Google login in your browser
        print("✓ Authenticated with Google!")

        # Test the protected tool
        result: Any = await client.call_tool("get_user_info")
        print(f"Google user: {result['email']}")
        print(f"Name: {result['name']}")


if __name__ == "__main__":
    asyncio.run(main())

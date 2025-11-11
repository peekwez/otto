import contextlib
from mcp.server.fastmcp import FastMCP, Context
from fastapi import FastAPI

mcp = FastMCP(
    name="demo",
    instructions="A simple demo plugin for FastMCP.",
)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code here
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())

        yield
    # Shutdown code here


api = FastAPI(
    name="demo_api",
    lifespan=lifespan,
)


@mcp.tool(name="TestTool")
def test_fool(context: Context) -> str:
    return '{"name": "Fool!"}'


api.mount("/demo", mcp.streamable_http_app())

# if __name__ == "__main__":

# def main():
#     print("Hello from demo!")

# api =

# @mcp.tool(name="TestTool")
# def test_fool(context: Context):
#     return "Fool!"


# def main():
#     print("Hello from demo!")


# if __name__ == "__main__":
#     main()

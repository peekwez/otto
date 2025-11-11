from mcp.server.fastmcp import Context, FastMCP

mcp = FastMCP(
    name="demo",
    instructions="A simple demo plugin for FastMCP.",
)


@mcp.tool(name="TestTool")
def test_fool(ctx: Context) -> str:
    return '{"name": "Fool!"}'

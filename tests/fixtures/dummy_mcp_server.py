"""Tiny standalone MCP server used by tests/test_mcp_client.py.

Run as a subprocess over stdio (that's what makes the integration test real
rather than mocked): `python dummy_mcp_server.py`.
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("dummy-test-server")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@mcp.tool()
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    mcp.run(transport="stdio")

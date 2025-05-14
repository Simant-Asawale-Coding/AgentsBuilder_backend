# MCP (Model Context Protocol) Documentation

## Overview
Model Context Protocol (MCP) is an open protocol that standardizes how applications (especially LLMs and AI agents) interact with external tools, resources, and data. It acts like a specialized API for LLMs, allowing them to call tools, access resources, and use prompts in a secure and consistent way.

### Key Concepts
- **Resources:** Like GET endpoints, for fetching data/context.
- **Tools:** Like POST endpoints, for executing functions or actions.
- **Prompts:** Templates for LLM interactions.

## Transport Mechanisms

### stdio (Standard Input/Output)
- Used for local integrations and command-line tools.
- Communication is via JSON-RPC messages sent over stdin (input) and stdout (output).
- Suitable for tools running locally, shell scripts, or CLI utilities.

**Python Example:**
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run_stdio()
```

### sse (Server-Sent Events)
- Used for networked, real-time communication, especially over HTTP.
- SSE allows the server to stream data to the client (one-way, server-to-client) in real time.
- The server exposes two endpoints:
    1. An SSE endpoint for clients to receive messages.
    2. An HTTP POST endpoint for clients to send messages.
- Security: Must validate Origin headers, bind to localhost for local dev, and implement authentication to prevent attacks (e.g., DNS rebinding).

**Python Example (Starlette):**
```python
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo")
sse = SseServerTransport("/messages")

async def handle_sse(scope, receive, send):
    async with sse.connect_sse(scope, receive, send) as streams:
        await mcp.run_with_streams(streams[0], streams[1])

async def handle_messages(scope, receive, send):
    await sse.handle_post_message(scope, receive, send)

starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ]
)
```

## Using fastmcp and Hosting MCP Servers
- Use `fastmcp` to define tools/resources with decorators (`@mcp.tool()`, `@mcp.resource()`).
- For local dev: Use stdio or run with a local HTTP server.
- For remote/public access: Deploy the Starlette/FastAPI app with the SSE endpoints to a cloud server (Azure, AWS, etc.).
- Once hosted, your custom tools are accessible via the MCP SSE URL, which can be used by LLMs, agents, or clients that support MCP.

## Security Best Practices
- Always validate Origin headers for SSE connections.
- Avoid binding to 0.0.0.0 for local dev; use localhost (127.0.0.1).
- Implement authentication for all SSE connections.

## Example: Creating an MCP Server with fastmcp
Below is a minimal example of creating an MCP server using the fastmcp package. This server exposes a simple addition tool and a greeting resource.

```python
# server.py
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("Demo")

# Define a tool (function) that adds two numbers
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

# Register the tool with the server
mcp.tool()(add)

# Define a resource for personalized greetings
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

# Register the resource with the server
mcp.resource("greeting://{name}")(get_greeting)

if __name__ == "__main__":
    # Run the server using stdio (for local/CLI integration)
    mcp.run_stdio()

    # Or, run with SSE/HTTP (for remote integration)
    # See the SSE example in the section above for Starlette/FastAPI integration
```

### Running the Example
- For local development (stdio):
  ```bash
  python server.py
  ```
- For SSE/HTTP (remote access):
  Integrate with Starlette/FastAPI as shown in the earlier SSE example.

## References
- [Model Context Protocol Official Site](https://modelcontextprotocol.io)
- [fastmcp PyPI](https://pypi.org/project/fastmcp/)
- [Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk)
- [MCP SSE Example Blog](https://blog.ni18.in/how-to-implement-a-model-context-protocol-mcp-server-with-sse/)

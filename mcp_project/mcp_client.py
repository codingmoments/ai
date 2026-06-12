"""MCP client: the Model Context Protocol half of the project.

Launches the MCP server over stdio, discovers its tools, and runs tool calls
on behalf of a caller. This isolates all MCP concerns (subprocess transport,
session lifecycle, tool discovery and invocation) from the AI chat logic.
"""

import json
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp.prompts import base
from pydantic import AnyUrl


class MCPClient:
  """Manages the MCP server subprocess, the session, and tool calls."""

  def __init__(self) -> None:
    self.session: ClientSession | None = None
    self._stack = AsyncExitStack()
    # Tool schemas in the OpenAI/Groq function-calling format, ready to be
    # passed straight to the model.
    self.tools: list[dict] = []

  async def start_and_connect_mcp_server(self) -> None:
    """Start the MCP server subprocess and discover its tools. Think of it as starting 
    up a helper program and opening a phone line to talk to it"""

    # Describe how to launch the server: run `uv run mcp_server.py`.
    # Nothing actually runs yet, this is just the instructions.
    params = StdioServerParameters(command="uv", args=["run", "mcp_server.py"])
    # The stdio transport spawns the server as a subprocess.
    # It connects the server's stdin/stdout to a pair of async channels/streams
    # that we can use to talk to it.
    # - read: messages coming from the server (server's stdout)
    # - write: messages sent to the server (server's stdin)
    read, write = await self._stack.enter_async_context(stdio_client(params))
    # Put the translator on top of the raw streams. Raw pipes are just byte
    # streams, but the MCP protocol is message-based and has framing.
    # ClientSession wraps them so both sides speak the same language and
    # handles the MCP protocol details (handshake, framing, etc).
    self.session = await self._stack.enter_async_context(ClientSession(read, write))
    # Perform the MCP initialization handshake, exchanging protocol versions and
    # capabilities with the server. This must complete before any other request.
    await self.session.initialize()

    # Ask the server what tools it offers
    listed = await self.session.list_tools()
    # Reshape each tool into the OpenAI/Groq function-calling format
    # so it can be handed straight to the model.
    self.tools = [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema,
            },
        }
        for tool in listed.tools
    ]

  async def call_tool(self, name: str, arguments: dict) -> str:
    """Run an MCP tool and return its text result."""
    assert self.session is not None
    # \033[90m turns the text grey; \033[0m resets the colour afterwards.
    print(f"\033[90mCalling tool {name} with arguments {arguments}\033[0m\n")
    result = await self.session.call_tool(name, arguments)
    # The result can hold several content blocks of different kinds (text,
    # images, etc). Keep only the text blocks and collect their text.
    parts = [c.text for c in result.content if getattr(
        c, "type", None) == "text"]
    return "\n".join(parts) if parts else "(no output)"

  # Get an MCP resource by URI. If it's JSON, parse it and return the data structure.
  async def get_resource(self, uri: str):
    """Read an MCP resource and return parsed JSON, or raw text otherwise."""
    assert self.session is not None
    # Read the resource from the server. The server will run the corresponding
    # @mcp.resource function and return the result as text.
    result = await self.session.read_resource(AnyUrl(uri))
    resource = result.contents[0]

    if resource.mimeType == "application/json":
      # If the resource is JSON, parse it and return the data structure.
      return json.loads(resource.text)
    else:
      return resource.text

  # List the prompts that the server offers
  async def list_prompts(self) -> list[types.Prompt]:
    """List the prompts that the MCP server offers."""
    assert self.session is not None
    result = await self.session.list_prompts()
    return result.prompts

  # Get a specific prompt by name, interpolating any arguments it needs.
  # If the server accepts 'path' as an argument, then this function should
  # be called with something like {"path": "data.txt"}.
  async def get_prompt(self, prompt_name: str, args: dict[str, str]) -> list[base.Message]:
    """Get a specific prompt by name, interpolating any arguments it needs."""
    assert self.session is not None
    result = await self.session.get_prompt(prompt_name, args)
    # The prompt result is a list of messages (like a chat conversation), 
    # which can be passed directly to the AI model as context.
    return result.messages

  async def close(self) -> None:
    await self._stack.aclose()

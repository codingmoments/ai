import asyncio
import os
from typing import Optional, Any
from contextlib import AsyncExitStack
# Core MCP SDK pieces: a client session, the params used to spawn a server over
# stdio, and shared type definitions (Tool, Prompt, CallToolResult, ...).
from mcp import ClientSession, StdioServerParameters, types
# Helper that launches an MCP server subprocess and talks to it over stdin/stdout.
from mcp.client.stdio import stdio_client


class MCPClient:
  """Thin wrapper around an MCP stdio connection to a single server.

  Holds the command used to launch the server, the live session once connected,
  and an AsyncExitStack that owns all async resources so they can be torn down
  together in cleanup().
  """

  def __init__(
      self,
      command: str,
      args: list[str],
      env: Optional[dict] = None,
  ):
    # How to launch the server process: the executable, its arguments, and an
    # optional environment override.
    self._command = command
    self._args = args
    self._env = env
    # Set once connect() succeeds; None means "not connected yet".
    self._session: Optional[ClientSession] = None
    # Collects every async context manager we open so aclose() can unwind them
    # all (subprocess + session) in the correct reverse order.
    self._exit_stack: AsyncExitStack = AsyncExitStack()

  @classmethod
  def for_document_server(cls) -> "MCPClient":
    # The one place that knows how to launch the document server: via "uv" if
    # USE_UV=1 in the environment, otherwise with plain "python". Both run the
    # same mcp_server.py file.
    if os.getenv("USE_UV", "0") == "1":
      command, args = "uv", ["run", "mcp_server.py"]
    else:
      command, args = "python", ["mcp_server.py"]
    return cls(command=command, args=args)

  async def connect(self):
    # Bundle the launch instructions into the structure the SDK expects.
    server_params = StdioServerParameters(
        command=self._command,
        args=self._args,
        env=self._env,
    )
    # Start the server subprocess and open the stdio channel to it. Registering
    # it on the exit stack means it gets shut down automatically during cleanup.
    stdio_transport = await self._exit_stack.enter_async_context(
        stdio_client(server_params)
    )
    # stdio_client yields a (read_stream, write_stream) pair.
    _stdio, _write = stdio_transport
    # Build the MCP session on top of those streams, again tracked by the exit
    # stack for orderly teardown.
    self._session = await self._exit_stack.enter_async_context(
        ClientSession(_stdio, _write)
    )
    # Perform the MCP handshake (capability/version negotiation) with the server.
    await self._session.initialize()

  def session(self) -> ClientSession:
    # Accessor that guarantees callers get a ready session, failing loudly if
    # connect() was never called.
    if self._session is None:
      raise ConnectionError(
          "Client session not initialized or cache not populated. Call connect_to_server first."
      )
    return self._session

  async def list_tools(self) -> list[types.Tool]:
    result = await self.session().list_tools()
    return result.tools

  async def call_tool(
      self, tool_name: str, tool_input: dict
  ) -> types.CallToolResult | None:
    print(f"Calling tool '{tool_name}' with input: {tool_input}")
    return await self.session().call_tool(tool_name, tool_input)

  async def list_prompts(self) -> list[types.Prompt]:
    # TODO: Return a list of prompts defined by the MCP server
    return []

  async def get_prompt(self, prompt_name, args: dict[str, str]):
    # TODO: Get a particular prompt defined by the MCP server
    return []

  async def read_resource(self, uri: str) -> Any:
    # TODO: Read a resource, parse the contents and return it
    return []

  # --- Async context-manager protocol: enables `async with MCPClient(...)` ---

  async def __aenter__(self):
    # Connect on entry and hand back the client for use inside the `with` block.
    await self.connect()
    return self

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    # On exit (normal or via exception), close every resource the exit stack is
    # holding (session + subprocess) and reset to the disconnected state.
    await self._exit_stack.aclose()
    self._session = None


# For testing: spin up the document server, connect, then immediately tear down.
async def main():
  async with MCPClient.for_document_server() as _client:
    result = await _client.list_tools()
    print("Tools available on server:")
    for tool in result:
      print(f" - {tool.name}: {tool.description}")
    result = await _client.call_tool("read_document_contents", {"doc_id": "outlook.pdf"})
    print(f"Document contents: {result}")


if __name__ == "__main__":
  # Entry point when run directly: drive the async main() to completion.
  asyncio.run(main())

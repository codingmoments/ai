import asyncio
import os
from typing import Optional, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


class MCPClient:
  def __init__(
      self,
      command: str,
      args: list[str],
      env: Optional[dict] = None,
  ):
    self._command = command
    self._args = args
    self._env = env
    self._session: Optional[ClientSession] = None
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
    server_params = StdioServerParameters(
        command=self._command,
        args=self._args,
        env=self._env,
    )
    stdio_transport = await self._exit_stack.enter_async_context(
        stdio_client(server_params)
    )
    _stdio, _write = stdio_transport
    self._session = await self._exit_stack.enter_async_context(
        ClientSession(_stdio, _write)
    )
    await self._session.initialize()

  def session(self) -> ClientSession:
    if self._session is None:
      raise ConnectionError(
          "Client session not initialized or cache not populated. Call connect_to_server first."
      )
    return self._session

  async def list_tools(self) -> list[types.Tool]:
    # TODO: Return a list of tools defined by the MCP server
    return []

  async def call_tool(
      self, tool_name: str, tool_input: dict
  ) -> types.CallToolResult | None:
    # TODO: Call a particular tool and return the result
    return None

  async def list_prompts(self) -> list[types.Prompt]:
    # TODO: Return a list of prompts defined by the MCP server
    return []

  async def get_prompt(self, prompt_name, args: dict[str, str]):
    # TODO: Get a particular prompt defined by the MCP server
    return []

  async def read_resource(self, uri: str) -> Any:
    # TODO: Read a resource, parse the contents and return it
    return []

  async def cleanup(self):
    await self._exit_stack.aclose()
    self._session = None

  async def __aenter__(self):
    await self.connect()
    return self

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    await self.cleanup()


# For testing
async def main():
  async with MCPClient.for_document_server() as _client:
    pass


if __name__ == "__main__":
  asyncio.run(main())

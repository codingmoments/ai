"""MCP server exposing a single tool: read_file.

Runs over stdio so an MCP client can launch it as a subprocess.
"""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("file-reader")


@mcp.tool(
    name="read_file",
    description="Read a text file from the local file system and return its contents."
)
def read_file(path: str) -> str:
  """Read a text file from the local file system and return its contents.

  Args:
      path: Path to the file (absolute, or relative to where the server runs).
  """
  file = Path(path).expanduser()
  if not file.exists():
    return f"Error: file not found: {path}"
  if not file.is_file():
    return f"Error: not a file: {path}"
  try:
    return file.read_text(encoding="utf-8", errors="replace")
  except OSError as exc:
    return f"Error reading file: {exc}"


if __name__ == "__main__":
  # Default transport is stdio.
  mcp.run()

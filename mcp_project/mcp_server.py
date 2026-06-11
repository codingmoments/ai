"""MCP server exposing a single tool: read_file.

Runs over stdio so an MCP client can launch it as a subprocess.
"""

from pathlib import Path

from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

mcp = FastMCP("file-reader")

employees = [
    {"id": 1, "name": "Alice", "role": "Engineer"},
    {"id": 2, "name": "Bob", "role": "Designer"},
    {"id": 3, "name": "Charlie", "role": "Product Manager"},
]


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


@mcp.resource(
    "resource://employees",
    mime_type="application/json"
)
def get_employees() -> list[dict[str, str]]:
  """Example resource that returns a JSON list of employees."""
  return employees


@mcp.resource(
    "resource://employees/{id}",
    mime_type="application/json"
)
def get_employee(id: int) -> dict[str, str] | None:
  """Example resource that returns a JSON dict for a single employee."""
  for employee in employees:
    if employee["id"] == id:
      return employee
  raise ValueError(f"Employee not found: {id}")


@mcp.prompt(
    name="format",
    description="Rewrites the contents of the document in a Markdown format."
)
def format_document(path: str = Field("Path to the file")) -> list[base.Message]:
  """Rewrites the contents of the document in a Markdown format.

  Args:
      path: Path to the file (absolute, or relative to where the server runs).
  """
  prompt = f"Your goal is to reformat the contents of the file at {path} into a Markdown format. " \
      "Please read the file and rewrite its contents in Markdown. " \
      "You can use headings, lists, code blocks, and other Markdown features to improve the readability of the document. " \
      "Make sure to preserve the original meaning and information while enhancing the structure and presentation. " \
      "Once you have reformatted the document, return the Markdown content as a string."
  return [base.UserMessage(prompt)]


if __name__ == "__main__":
  # Default transport is stdio.
  mcp.run()

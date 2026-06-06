from pydantic import Field
from mcp.server.fastmcp import FastMCP

docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

# Create the MCP server instance everything registers onto. "DocumentMCP" is the
# name it announces to clients during the handshake; log_level="ERROR" silences
# INFO/DEBUG chatter so it can't pollute the stdio channel carrying the protocol.
mcp = FastMCP("DocumentMCP", log_level="ERROR")


# Expose a tool the AI can call to read one document's text.
# @mcp.tool registers this function with the server; the name/description tell
# the model what it does, and FastMCP turns the type-hinted parameters (with
# their Field descriptions) into the JSON input schema sent to the client.
@mcp.tool(
    name="read_document_contents",
    description="Read the contents of a document and return it as a string."
)
def read_document_contents(
    doc_id: str = Field(description="The ID of the document to read.")
) -> str:
  """Read the contents of a document and return it as a string."""
  if doc_id not in docs:
    raise ValueError(f"Document with id '{doc_id}' not found.")
  return docs[doc_id]


@mcp.tool(
    name="edit_document",
    description="Edit a document by replacing a string in the document's content with a new string."
)
def edit_document(
    doc_id: str = Field(description="The ID of the document to edit."),
    old_string: str = Field(description="The text to be replaced."),
    new_string: str = Field(description="The text to replace with.")
) -> str:
  """Edit a document by replacing a string in the document's content with a new string."""
  if doc_id not in docs:
    raise ValueError(f"Document with id '{doc_id}' not found.")
  docs[doc_id] = docs[doc_id].replace(old_string, new_string)
  return docs[doc_id]


# TODO: Write a resource to return all doc id's
# TODO: Write a resource to return the contents of a particular doc
# TODO: Write a prompt to rewrite a doc in markdown format
# TODO: Write a prompt to summarize a doc
if __name__ == "__main__":
  mcp.run(transport="stdio")

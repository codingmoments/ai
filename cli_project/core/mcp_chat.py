from typing import List, Tuple
from mcp.types import Prompt, PromptMessage

from core.chat import Chat
from core.messenger import Messenger
from mcp_client import MCPClient


# A document-aware version of Chat. On top of the basic conversation loop it
# inherits from Chat, this class adds two extra abilities driven by what the
# user types:
#   * "@doc_id"  -> pull that document's text into the prompt as context.
#   * "/command" -> run a ready-made prompt template stored on the MCP server.
# It talks to an MCP "doc server" (self.doc_client) to fetch those documents
# and prompt templates.
class MCPChat(Chat):
  def __init__(
      self,
      doc_client: MCPClient,
      messenger: Messenger,
  ):
    # Hand the shared pieces (AI messenger + tool client) to the base Chat,
    # which sets up the conversation history and the main loop.
    super().__init__(messenger=messenger, client=doc_client)

    # The one MCP client we use specifically for documents and prompts.
    self.doc_client: MCPClient = doc_client

  # Ask the doc server for the list of ready-made prompt templates (the things
  # the user can trigger with a "/command").
  async def list_prompts(self) -> list[Prompt]:
    return await self.doc_client.list_prompts()

  # Ask the doc server for the ids/names of every document it knows about.
  async def list_docs_ids(self) -> list[str]:
    return await self.doc_client.read_resource("docs://documents")

  # Fetch the full text of one document by its id.
  async def get_doc_content(self, doc_id: str) -> str:
    return await self.doc_client.read_resource(f"docs://documents/{doc_id}")

  # Fetch a filled-in prompt template from the server for the given command,
  # passing along which document it should act on.
  async def get_prompt(
      self, command: str, doc_id: str
  ) -> list[PromptMessage]:
    return await self.doc_client.get_prompt(command, {"doc_id": doc_id})

  # Look at the user's text, find any "@document" mentions, fetch those
  # documents, and return their contents wrapped in <document> tags so the AI
  # can read them as context.
  async def _extract_resources(self, query: str) -> str:
    # Pull out every word starting with "@" and drop the "@" itself.
    # e.g. "summarize @report.docx" -> ["report.docx"]
    mentions = [word[1:] for word in query.split() if word.startswith("@")]

    # Get the list of real documents so we only fetch ones that actually exist.
    doc_ids = await self.list_docs_ids()
    mentioned_docs: list[Tuple[str, str]] = []

    # For each known document, if the user mentioned it, fetch its content.
    for doc_id in doc_ids:
      if doc_id in mentions:
        content = await self.get_doc_content(doc_id)
        mentioned_docs.append((doc_id, content))

    # Stitch all the fetched documents into one string of <document> blocks.
    return "".join(
        f'\n<document id="{doc_id}">\n{content}\n</document>\n'
        for doc_id, content in mentioned_docs
    )

  # Handle a "/command" message (e.g. "/summarize report.docx") by loading the
  # matching prompt template from the server and adding it to the conversation.
  async def _process_command(self, query: str):
    # Split into words: words[0] is the command, words[1] is the document id.
    words = query.split()
    # Strip the leading slash to get the bare command name, e.g. "/summarize" -> "summarize".
    command = words[0].replace("/", "")

    # Ask the server to build the prompt for this command + document.
    # NOTE: this assumes a document id was provided; "/summarize" with no
    # second word would fail when reading words[1].
    messages = await self.doc_client.get_prompt(
        command, {"doc_id": words[1]}
    )

    # The server returns MCP-format messages; convert them to the plain
    # dictionaries the AI expects, then add them to the conversation history.
    self.conversation.add_message_params(
        convert_prompt_messages_to_message_params(messages)
    )

  # The main entry point: runs for every message the user types. It decides
  # whether the message is a command or a normal question, then prepares the
  # conversation accordingly. (This overrides the simpler version in Chat.)
  async def _process_query(self, query: str):
    # If it starts with "/", treat it as a command and stop here.
    if query.startswith("/"):
      await self._process_command(query)
      return

    # Otherwise, gather the text of any "@mentioned" documents.
    added_resources = await self._extract_resources(query)

    # Wrap the user's question together with the document context and clear
    # instructions, so the AI answers using the docs without mentioning them.
    prompt = f"""{query}"""

    # Add the assembled prompt to the conversation as the user's message.
    self.conversation.add_user_message(prompt)


def _get_field(item, key: str, default=None):
  """Read a field from `item`, whether it's a dict or a custom object.

  This is the ONE place that knows about the dict-vs-object difference,
  so the rest of the code doesn't have to keep re-checking it.
  """
  # A dictionary stores values under keys -> read with .get().
  if isinstance(item, dict):
    return item.get(key, default)
  # A normal object stores values as attributes -> read with getattr().
  if hasattr(item, "__dict__"):
    return getattr(item, key, default)
  # Anything else (e.g. a plain string/number) has no such field.
  return default


# Convert ONE message from the MCP server's format into the plain
# {"role": ..., "content": ...} dictionary the AI model understands.
def convert_prompt_message_to_message_param(
    prompt_message: "PromptMessage",
) -> dict:
  # The AI only knows two roles; treat anything that isn't "user" as "assistant".
  role = "user" if prompt_message.role == "user" else "assistant"
  content = prompt_message.content

  # Case 1: content is a single text block.
  if _get_field(content, "type") == "text":
    return {"role": role, "content": _get_field(content, "text", "")}

  # Case 2: content is a list of blocks — keep only the text ones.
  if isinstance(content, list):
    text_blocks = [
        {"type": "text", "text": _get_field(item, "text", "")}
        for item in content
        if _get_field(item, "type") == "text"
    ]
    if text_blocks:
      return {"role": role, "content": text_blocks}

  # Case 3: nothing usable — return empty text.
  return {"role": role, "content": ""}


# Convert a WHOLE list of server messages by running the single-message
# converter on each one.
def convert_prompt_messages_to_message_params(prompt_messages: List[PromptMessage]) -> List[dict]:
  return [
      convert_prompt_message_to_message_param(msg) for msg in prompt_messages
  ]

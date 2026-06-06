import asyncio
import os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_client import MCPClient
from core.messenger import Messenger
from core.mcp_chat import MCPChat
from core.cli import CliApp

# Read settings from a local ".env" file into environment variables, so things
# like the model name and API key don't have to be hard-coded.
load_dotenv()

# Groq Config: which AI model to use, read from the .env file.
groq_model = os.getenv("GROQ_MODEL", "")
# Stop early with a clear message if the model wasn't configured.
assert groq_model, "Error: GROQ_MODEL cannot be empty. Update .env"


# Sets up every part of the app and then starts it. This is "async" because
# talking to the AI and the document server happens over the network/processes.
async def main():
  # The object that sends messages to the Groq AI and gets replies back.
  messenger = Messenger(model=groq_model)

  # AsyncExitStack makes sure the document server is shut down cleanly when we
  # exit this block, even if an error happens.
  async with AsyncExitStack() as stack:
    # Start the MCP document server as a separate process and connect to it.
    # MCPClient decides internally how to launch it (uv vs python).
    doc_client = await stack.enter_async_context(
        MCPClient.for_document_server()
    )

    # The document-aware chat engine: ties the AI, the document server, and the
    # conversation history together.
    chat = MCPChat(
        doc_client=doc_client,
        messenger=messenger,
    )

    # Wrap the chat in the command-line interface and start the input loop.
    # This runs until the user presses Ctrl+C.
    cli = CliApp(chat)
    await cli.run()


# This block only runs when you start the file directly (python main.py),
# not when it's imported by another file. It's the program's entry point.
if __name__ == "__main__":
  # On Windows, asyncio already uses the Proactor event loop by default
  # (since Python 3.8), so no special policy setup is needed here.
  # asyncio.run(...) starts the async main() function above.
  asyncio.run(main())

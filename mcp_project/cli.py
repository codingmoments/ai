"""Terminal CLI: chat with the AI, which can read local files via the MCP tool.

Run with:  uv run mcp-chat      (or)   uv run python cli.py
Type 'exit' or 'quit' to leave.
"""

import asyncio
import json
from dotenv import load_dotenv
from ai_messenger import AIMessenger


async def handle_command(aiMessenger: AIMessenger, command: str) -> None:
  """Handle a /slash command by reading an MCP resource directly.

  Unlike tools (which the model decides to call), resources are read by the
  application itself, so these commands never go through the AI at all.
  """
  parts = command.split()
  name, args = parts[0].lower(), parts[1:]
  if name == "/employees" and not args:
    uri = "resource://employees"
  elif name == "/employee" and len(args) == 1:
    uri = f"resource://employees/{args[0]}"
  else:
    print("Commands: /employees, /employee <id>\n")
    return
  try:
    data = await aiMessenger.get_resource(uri)
  except Exception as exc:
    print(f"Error reading {uri}: {exc}\n")
    return
  answer = await aiMessenger.ask("Format this data in a tabular format, "
                                 "headers should be all capitals"
                                 f"and all columns should be aligned in same line: {json.dumps(data)}")
  print(f"\033[32mai>\033[0m\n")
  print(f"\033[32m{answer}\033[0m\n")


async def chat_loop() -> None:
  aiMessenger = AIMessenger()
  await aiMessenger.initialize()
  print("Connected. Ask me anything (I can read local files). Type 'exit' to quit.")
  print("Resource commands: /employees, /employee <id>\n")
  try:
    while True:
      try:
        # \033[32m turns the text green
        user_input = input("\033[32myou> ").strip()
        # Reset the colour back to default after the input
        print("\033[0m", end="", flush=True)
      except (EOFError, KeyboardInterrupt):
        print()
        break
      if not user_input:
        continue
      if user_input.lower() in {"exit", "quit"}:
        break
      # Slash commands read MCP resources directly: no AI round-trip.
      if user_input.startswith("/"):
        await handle_command(aiMessenger, user_input)
        continue
      # Send the user's message to the AI and print the response.
      print(f"\033[90mSending to AI: {user_input}\033[0m\n")
      answer = await aiMessenger.ask(user_input)
      print(f"\033[32mai> {answer}\033[0m\n")
  finally:
    await aiMessenger.close()
    print("Bye.")


def main() -> None:
  load_dotenv()
  asyncio.run(chat_loop())


if __name__ == "__main__":
  main()

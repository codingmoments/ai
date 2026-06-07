"""Terminal CLI: chat with the AI, which can read local files via the MCP tool.

Run with:  uv run mcp-chat      (or)   uv run python cli.py
Type 'exit' or 'quit' to leave.
"""

import asyncio
from dotenv import load_dotenv
from ai_messenger import AIMessenger


async def chat_loop() -> None:
  aiMessenger = AIMessenger()
  await aiMessenger.initialize()
  print("Connected. Ask me anything (I can read local files). Type 'exit' to quit.\n")
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
      # Send the user's message to the AI and print the response.
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

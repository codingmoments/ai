from prompt_toolkit import PromptSession

from core.mcp_chat import MCPChat


# The command-line interface: the thin layer you actually type into. Its only
# job is the read -> ask -> print loop. All the real work (understanding
# "@documents" and "/commands", talking to the AI) is done by the agent.
class CliApp:
  def __init__(self, agent: MCPChat):
    # The chat engine that does the real work for each message.
    self.agent = agent
    # A prompt_toolkit input session: gives us an async prompt plus niceties
    # like arrow-key history and line editing for free.
    self.session = PromptSession()

  # The main loop: keep reading input and answering until the user quits.
  async def run(self):
    while True:
      try:
        # Wait for the user to type a line and press Enter ("> " is the prompt).
        user_input = await self.session.prompt_async("> ")
        # Ignore empty lines (just whitespace) and ask again.
        if not user_input.strip():
          continue

        # Hand the message to the agent, which handles documents/commands,
        # talks to the AI, and returns the final answer.
        response = await self.agent.run(user_input)
        print(f"\nResponse:\n{response}")

      # Ctrl+C cleanly exits the loop instead of crashing.
      except KeyboardInterrupt:
        break

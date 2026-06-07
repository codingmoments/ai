"""The AI half of the project: a Groq-backed chat agent with tool calling.

``AIMessenger`` holds the conversation history and, on each ``ask``, sends it
to the Groq model with the MCP tools advertised as callable functions. When the
model requests a tool, the messenger runs it via the ``MCPClient``, feeds the
result back, and loops until the model returns a plain text answer. All MCP
transport details live in ``mcp_client.py``.
"""

import json
import os

from groq import Groq

from mcp_client import MCPClient

SYSTEM_PROMPT = (
    "You are a helpful assistant. You can read local files using the read_file "
    "tool. When the user asks about a file's contents, call the tool to get the "
    "actual contents instead of guessing."
)


class AIMessenger:
  """Holds the Groq client and conversation state, and runs chat turns."""

  def __init__(self) -> None:
    api_key = os.environ.get("GROQ_API_KEY")
    self.groq = Groq(api_key=api_key)
    self.mcp_client = MCPClient()
    # Placing the system prompt as the first message ensures the model sees it
    # and is reminded of its role and tool-use policy on every turn.
    self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

  async def initialize(self) -> None:
    """Start and connect to the MCP server so its tools become available to the AI."""
    await self.mcp_client.start_and_connect_mcp_server()

  async def ask(self, user_input: str) -> str:
    """Send one user message through the model, handling any tool calls."""

    # As the chat proceeds, ask() appends user, assistant, and tool messages onto this same
    # list so the model gets the full conversation history and can decide when to call tools
    # vs. answer directly.
    self.messages.append({"role": "user", "content": user_input})

    while True:
      try:
        # Send the full conversation to the model, advertising the MCP tools so
        # it can either answer directly or request a tool call.
        response = self.groq.chat.completions.create(
            model=os.environ.get("GROQ_LLM_MODEL"),
            messages=self.messages,
            tools=self.mcp_client.tools,
            tool_choice="auto",
        )
      except Exception as exc:
        return f"Error talking to the AI: {exc}"
      message = response.choices[0].message

      # No tool calls means the model produced its final answer: record it in
      # the history and return it to the caller, ending the loop.
      if not message.tool_calls:
        self.messages.append({"role": "assistant", "content": message.content})
        return message.content or ""

      # The model wants to call tools. Record its request (the assistant turn,
      # including the list of requested tool calls) in the history so the next
      # API call has the matching context for the tool results we add below.
      self.messages.append(
          {
              "role": "assistant",
              "content": message.content or "",
              "tool_calls": [
                  {
                      "id": tc.id,
                      "type": "function",
                      "function": {
                          "name": tc.function.name,
                          "arguments": tc.function.arguments,
                      },
                  }
                  for tc in message.tool_calls
              ],
          }
      )

      # Execute each requested tool via the MCP client and append its output as
      # a "tool" message (linked back by tool_call_id), so the next loop pass
      # lets the model read the results and continue.
      for tc in message.tool_calls:
        print(
            f"Model requested tool call {tc.function.name} with args {tc.function.arguments}")
        args = json.loads(tc.function.arguments or "{}")
        output = await self.mcp_client.call_tool(tc.function.name, args)
        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": tc.id,
                "content": output,
            }
        )
      # Loop again so the model can use the tool results.

  async def close(self) -> None:
    await self.mcp_client.close()

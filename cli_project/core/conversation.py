from groq.types.chat import ChatCompletion


# Owns the conversation history (the list of messages sent to the AI).
# This is the ONLY place that is allowed to change that list, so all the
# logic for "how do we add a message" lives here in one spot.
class Conversation:
  def __init__(self):
    # The conversation history / memory. Every message gets appended here so
    # the AI remembers what was said earlier. Starts empty.
    self._messages: list[dict] = []

  # Returns the live list of messages to send to the AI.
  # Note: callers should only read this, not mutate it directly.
  def messages(self) -> list[dict]:
    return self._messages

  # Adds something the user typed, tagged as the "user" role.
  def add_user_message(self, content: str) -> None:
    self._messages.append({"role": "user", "content": content})

  # Adds the AI's reply to the history, including any tool calls it requested.
  # This knows the Groq-specific shape of an assistant message.
  def add_assistant_message(self, response: ChatCompletion) -> None:
    msg = response.choices[0].message
    assistant_message = {"role": "assistant", "content": msg.content}
    if msg.tool_calls:
      assistant_message["tool_calls"] = [
          {
              "id": tc.id,
              "type": "function",
              "function": {
                  "name": tc.function.name,
                  "arguments": tc.function.arguments,
              },
          }
          for tc in msg.tool_calls
      ]
    self._messages.append(assistant_message)

  # Adds the results returned by MCP tools back into the history.
  def add_tool_results(self, parts: list[dict]) -> None:
    self._messages.extend(parts)

  # Adds pre-built message dicts (e.g. from an MCP prompt command).
  def add_message_params(self, params: list[dict]) -> None:
    self._messages.extend(params)

  # Clears the conversation history.
  def clear(self) -> None:
    self._messages.clear()
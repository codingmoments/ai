from groq import Groq

class Messenger:
  def __init__(self, model: str):
    self.client = Groq()
    self.model = model

  # Adds tool results returned by MCP tools back into the conversation history.
  def add_tool_results(self, messages: list, tool_results: list):
    messages.extend(tool_results)

  # Adds the AI's reply to the conversation history, including any tool calls it requested.
  def add_assistant_message(self, messages: list, response):
    msg = response.choices[0].message
    assistant_message = {"role": "assistant", "content": msg.content}
    if msg.tool_calls:
      assistant_message["tool_calls"] = [
          {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
          for tc in msg.tool_calls
      ]
    messages.append(assistant_message)

  # Extracts the plain text from the AI's response.
  def text_from_message(self, response) -> str:
    return response.choices[0].message.content or ""

  # Sends the conversation history to the Groq API and returns the AI's response.
  def chat(self, messages, system=None, temperature=1.0, tools=None):
    all_messages = messages
    if system:
      all_messages = [{"role": "system", "content": system}] + messages

    params = {
        "model": self.model,
        "max_tokens": 8000,
        "messages": all_messages,
        "temperature": temperature,
    }

    if tools:
      params["tools"] = tools

    return self.client.chat.completions.create(**params)
from groq import Groq

class Claude:
  def __init__(self, model: str):
    self.client = Groq()
    self.model = model

  def add_user_message(self, messages: list, message):
    if isinstance(message, list) and all(
        isinstance(m, dict) and m.get("role") == "tool" for m in message
    ):
      messages.extend(message)
    else:
      content = message if isinstance(message, str) else str(message)
      messages.append({"role": "user", "content": content})

  def add_assistant_message(self, messages: list, response):
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
    messages.append(assistant_message)

  def text_from_message(self, response) -> str:
    return response.choices[0].message.content or ""

  def chat(
      self,
      messages,
      system=None,
      temperature=1.0,
      stop_sequences=[],
      tools=None,
      thinking=False,
      thinking_budget=1024,
  ):
    all_messages = messages
    if system:
      all_messages = [{"role": "system", "content": system}] + messages

    params = {
        "model": self.model,
        "max_tokens": 8000,
        "messages": all_messages,
        "temperature": temperature,
    }

    if stop_sequences:
      params["stop"] = stop_sequences

    if tools:
      params["tools"] = tools

    return self.client.chat.completions.create(**params)

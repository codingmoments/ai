from groq import Groq
from groq.types.chat import ChatCompletion

class Messenger:
  def __init__(self, model: str):
    self.client = Groq()
    self.model = model

  # Extracts the plain text from the AI's response.
  def text_from_message(self, response: ChatCompletion) -> str:
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

    print(f"Sending to model with params: {params}")

    return self.client.chat.completions.create(**params)
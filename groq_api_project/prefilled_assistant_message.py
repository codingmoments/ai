
from dotenv import load_dotenv
from groq import Groq

import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def add_user_message(messages: list[dict], content: str) -> None:
  messages.append({
      "role": "user",
      "content": content
  })


def add_assistant_message(messages: list[dict], content: str) -> None:
  messages.append({
      "role": "assistant",
      "content": content
  })


def chat(messages: list[dict]) -> str:
  response = client.chat.completions.create(
      messages=messages,
      model=os.getenv("GROQ_API_MODEL"),
      # Using the stop parameter to end the
      # response at the closing code block
      stop="```"
  )
  return response.choices[0].message.content


# conversation history; each dict is one turn
messages: list[dict] = []

add_user_message(
    messages, "Write a Python function to calculate the factorial of a number.")
# Prefilling the assistant message with the opening
# code block to guide the model to respond with code
add_assistant_message(
    messages, "Here are all the possible solutions in Python:\n```python")

answer = chat(messages)

print(f"AI: {answer}")
add_assistant_message(messages, answer)

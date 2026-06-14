
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
      model=os.getenv("GROQ_API_MODEL")
  )
  return response.choices[0].message.content


# conversation history; each dict is one turn
messages: list[dict] = []

add_user_message(
    messages, "Define quantum computing in one sentence.")

answer = chat(messages)

print(answer, "\n")

add_assistant_message(messages, answer)

add_user_message(
    messages, "Write another sentence.")

answer = chat(messages)

print(answer, "\n")

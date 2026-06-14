
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

while True:
  user_input = input("User: ")
  if user_input.lower() in ["exit", "quit"]:
    print("Exiting the chat.")
    break

  add_user_message(messages, user_input)

  answer = chat(messages)

  print(f"AI: {answer}")
  add_assistant_message(messages, answer)

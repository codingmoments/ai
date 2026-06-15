
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


def chat(messages: list[dict]):
  stream = client.chat.completions.create(
      messages=messages,
      model=os.getenv("GROQ_API_MODEL"),
      stream=True
  )
  return stream


# conversation history; each dict is one turn
messages: list[dict] = []

# Add a system message to set the behavior of the assistant
messages.append({
    "role": "system",
    "content": "Answer in at least 5 sentences and at most 10 sentences."
})

while True:
  user_input = input("User: ")
  if user_input.lower() in ["exit", "quit"]:
    print(messages, "\n")
    print("Exiting the chat.")
    break

  add_user_message(messages, user_input)

  stream = chat(messages)

  print("AI: ", end="", flush=True)
  chunks = []
  for event in stream:
    if event.choices[0].delta.content:
      chunks.append(event.choices[0].delta.content)
      print(event.choices[0].delta.content, end="", flush=True)

  print()

  add_assistant_message(messages, "".join(chunks))

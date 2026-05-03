import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# System messages are a way to give the model a “persona” or instruction that stays the same for the whole conversation.
messages = [
    {"role": "system", "content": "You are a helpful Python tutor who explains in very simple language with examples."}
]

while True:

  user_input = input("Paste your code: ")

  if user_input.lower() == "exit":
    break

  messages.append({
      "role": "user",
      "content": f"Explain this code in simple terms, give example and real-world use:\n{user_input}"
  })

  response = client.chat.completions.create(
      model="openai/gpt-oss-120b", messages=messages
  )

  print("AI:", response.choices[0].message.content)

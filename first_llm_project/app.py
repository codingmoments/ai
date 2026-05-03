import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

while True:

  user_input = input("Paste your notes: ")

  if user_input.lower() == "exit":
    break

  messages = [{
      "role": "user",
      "content": f"""
        Summarize the following text in:
        1. Simple explanation
        2. Key bullet points
        3. Real-world use

        Text:
        {user_input}
        """
  }]

  response = client.chat.completions.create(
      model="openai/gpt-oss-120b", messages=messages
  )

  print("\n\nAI summary:", response.choices[0].message.content)

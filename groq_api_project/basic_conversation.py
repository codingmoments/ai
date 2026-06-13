'''This is a basic example of how to use the Groq API to have a conversation with a language model.
Make sure to set your GROQ_API_KEY and GROQ_API_MODEL in your .env file before running this code.
'''

from dotenv import load_dotenv
from groq import Groq

import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "What is quantum computing? Explain it to me like I'm 5 years old."
        }
    ],
    model=os.getenv("GROQ_API_MODEL")
)

print(response.choices[0].message.content)

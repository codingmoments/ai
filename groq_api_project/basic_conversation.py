'''This is a basic example of how to use the Groq API to have a conversation with a language model.
Make sure to set your GROQ_API_KEY and GROQ_API_MODEL in your .env file before running this code.
'''

# reads key=value pairs from .env into os.environ
from dotenv import load_dotenv
# Groq client class for making API calls
from groq import Groq

# needed to access environment variables at runtime
import os

# parses .env file and populates os.environ before any getenv calls
load_dotenv()

# authenticates the client with the secret API key
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# sends a blocking chat completion request to Groq
response = client.chat.completions.create(
    # conversation history; each dict is one turn
    messages=[
        {  # single user turn
            "role": "user",  # identifies the speaker as the human user
            # the prompt sent to the model
            "content": "What is quantum computing? Explain it to me like I'm 5 years old."
        }
    ],
    # model ID pulled from .env, e.g. "llama3-8b-8192"
    model=os.getenv("GROQ_API_MODEL")
)

# prints the first (and only) completion the model returned
print(response.choices[0].message.content)

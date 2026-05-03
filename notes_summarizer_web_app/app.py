import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.title("🧠 AI Notes Summarizer")

user_input = st.text_area("Paste your text here:")

if st.button("Summarize"):
  if user_input:
    with st.spinner("Thinking..."):

      response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
          {
            "role": "user",
            "content": f"""
              Summarize the following text in:
              1. Simple explanation
              2. Key bullet points
              3. Real-world use

              Text:
              {user_input}
              """
          }
        ]
      )

      result = response.choices[0].message.content

      st.subheader("📄 Summary")
      st.write(result)

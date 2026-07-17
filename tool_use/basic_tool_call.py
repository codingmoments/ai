"""
 This program demonstrates how to use tool call with the Groq API.
 We will use a simple tool that returns the current date and time in a specified format. 
 The program shows how to define the tool, provide its JSON schema, and handle the tool call in conversation with the Groq API.
 Run the program using the command: `python basic_tool_call.py` OR `uv run basic_tool_call.py`
"""

from datetime import datetime, timedelta
from dotenv import load_dotenv
from groq import Groq

import json
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Tool: get_current_datetime
def get_current_datetime(date_format="%Y-%m-%d %H:%M:%S"):
  if not date_format:
    raise ValueError("date_format must be a non-empty string")
  return datetime.now().strftime(date_format)


# Tool JSON schema for get_current_datetime
get_current_datetime_schema = {
    "type": "function",
    "function": {
        "name": "get_current_datetime",
        "description": "Returns the current local date and time, formatted according to a Python strftime format string. Use this whenever you need the present date, time, or both (for example, to timestamp an action, answer 'what time is it', or compute how far away a future date is). The value reflects the moment the tool is called, in the server's local timezone.",
        "parameters": {
            "type": "object",
            "properties": {
                "date_format": {
                    "type": "string",
                    "description": "A Python strftime format string that controls how the datetime is rendered. Must be a non-empty string. Common directives: %Y (4-digit year), %m (month 01-12), %d (day 01-31), %H (hour 00-23), %M (minute), %S (second). Examples: '%Y-%m-%d %H:%M:%S' -> '2026-07-14 09:30:00'; '%Y-%m-%d' -> '2026-07-14'; '%H:%M' -> '09:30'. Omit to use the default '%Y-%m-%d %H:%M:%S'.",
                    "default": "%Y-%m-%d %H:%M:%S",
                    "minLength": 1
                }
            },
            "required": []
        }
    }
}

messages = []

# Add a user message asking for the current date and time in a specific format
messages.append(
    {
        "role": "user",
        "content": "What is the exact current date and time, formatted as '%d-%m-%Y %H:%M:%S'?"
    }
)

# Call the Groq API with the user message and the get_current_datetime tool schema
response = client.chat.completions.create(
    messages=messages,
    model=os.getenv("GROQ_API_MODEL"),
    tools=[get_current_datetime_schema]
)

# Check if the response contains a tool call
if response.choices[0].message.tool_calls:
  # Append the assistant's message to the conversation history
  messages.append(response.choices[0].message)

  tool_call = response.choices[0].message.tool_calls[0]
  tool_name = tool_call.function.name
  tool_args = json.loads(tool_call.function.arguments)

  if tool_name == "get_current_datetime":
    date_format = tool_args.get("date_format", "%Y-%m-%d %H:%M:%S")
    # Call the tool function
    tool_result = get_current_datetime(date_format)

    # Append the tool result to the conversation history
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": tool_result,
        }
    )

    # Call the Groq API again to get the final response after the tool call
    final_response = client.chat.completions.create(
        messages=messages,
        model=os.getenv("GROQ_API_MODEL"),
        tools=[get_current_datetime_schema]
    )

    print("Final response from Groq API:")
    print(final_response.choices[0].message.content)

"""
 This program demonstrates multi-turn tool call with the Groq API.
 Run the program using the command: `python multi_turn_tool_call.py` OR `uv run multi_turn_tool_call.py`
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


def text_from_message(chatCompletion):
    return "\n".join(
        [choice.message.content for choice in chatCompletion.choices if choice.message.content]
    )


def add_user_message(messages, content):
    messages.append(
        {
            "role": "user",
            "content": content
        }
    )


def add_assistant_message(messages, chatCompletion):
    message = {
        "role": "assistant",
        "content": text_from_message(chatCompletion),
    }

    tool_calls = chatCompletion.choices[0].message.tool_calls
    if tool_calls:
        message["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in tool_calls
        ]

    messages.append(message)


def chat_with_tool_call(messages, tools=None):
    params = {
        "messages": messages,
        "model": os.getenv("GROQ_API_MODEL"),
    }

    if tools:
        params["tools"] = tools

    return client.chat.completions.create(**params)


def run_tool(tool_name, tool_args):
    if tool_name == "get_current_datetime":
        return get_current_datetime(**tool_args)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def run_tools(chatCompletion):
    tool_requests = chatCompletion.choices[0].message.tool_calls

    tool_results = []

    for tool_request in tool_requests:
        tool_name = tool_request.function.name
        tool_args = json.loads(tool_request.function.arguments)

        try:
            result = run_tool(tool_name, tool_args)

            tool_result = {
                "role": "tool",
                "tool_call_id": tool_request.id,
                "content": result,
            }
            tool_results.append(tool_result)
        except Exception as e:
            tool_result = {
                "role": "tool",
                "tool_call_id": tool_request.id,
                "content": "An error has occurred - " + str(e),
            }
            tool_results.append(tool_result)

    return tool_results


def run_conversations(messages):
    while True:
        response = chat_with_tool_call(
            messages, tools=[get_current_datetime_schema])

        add_assistant_message(messages, response)

        if response.choices[0].finish_reason != "tool_calls":
            break

        tool_results = run_tools(response)

        messages.extend(tool_results)

    return messages


messages = run_conversations([
    {
        "role": "user",
        "content": "What is the exact current date and time, formatted as '%d-%m-%Y %H:%M:%S'? And what is current time in %H:%M' format?"
    }
])

print("Final conversation history:")
for message in messages:
    print(f"{message['role']}: {message['content']}")

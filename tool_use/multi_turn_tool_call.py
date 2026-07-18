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


def get_current_datetime(date_format="%Y-%m-%d %H:%M:%S"):
    """
    Tool: get_current_datetime
    """
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


def add_duration_to_datetime(
    datetime_str, duration=0, unit="days", input_format="%Y-%m-%d"
):
    """
    Tool: add_duration_to_datetime
    """
    date = datetime.strptime(datetime_str, input_format)

    if unit == "seconds":
        new_date = date + timedelta(seconds=duration)
    elif unit == "minutes":
        new_date = date + timedelta(minutes=duration)
    elif unit == "hours":
        new_date = date + timedelta(hours=duration)
    elif unit == "days":
        new_date = date + timedelta(days=duration)
    elif unit == "weeks":
        new_date = date + timedelta(weeks=duration)
    elif unit == "months":
        month = date.month + duration
        year = date.year + month // 12
        month = month % 12
        if month == 0:
            month = 12
            year -= 1
        day = min(
            date.day,
            [
                31,
                29 if year % 4 == 0 and (
                    year % 100 != 0 or year % 400 == 0) else 28,
                31,
                30,
                31,
                30,
                31,
                31,
                30,
                31,
                30,
                31,
            ][month - 1],
        )
        new_date = date.replace(year=year, month=month, day=day)
    elif unit == "years":
        new_date = date.replace(year=date.year + duration)
    else:
        raise ValueError(f"Unsupported time unit: {unit}")

    return new_date.strftime("%A, %B %d, %Y %I:%M:%S %p")


# Tool JSON schema for add_duration_to_datetime
add_duration_to_datetime_schema = {
    "type": "function",
    "function": {
        "name": "add_duration_to_datetime",
        "description": "Adds a specified duration to a datetime string and returns the resulting datetime in a detailed format. This tool converts an input datetime string to a Python datetime object, adds the specified duration in the requested unit, and returns a formatted string of the resulting datetime. It handles various time units including seconds, minutes, hours, days, weeks, months, and years, with special handling for month and year calculations to account for varying month lengths and leap years. The output is always returned in a detailed format that includes the day of the week, month name, day, year, and time with AM/PM indicator (e.g., 'Thursday, April 03, 2025 10:30:00 AM').",
        "parameters": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "The input datetime string to which the duration will be added. This should be formatted according to the input_format parameter.",
                },
                "duration": {
                    "type": "number",
                    "description": "The amount of time to add to the datetime. Can be positive (for future dates) or negative (for past dates). Defaults to 0.",
                },
                "unit": {
                    "type": "string",
                    "description": "The unit of time for the duration. Must be one of: 'seconds', 'minutes', 'hours', 'days', 'weeks', 'months', or 'years'. Defaults to 'days'.",
                },
                "input_format": {
                    "type": "string",
                    "description": "The format string for parsing the input datetime_str, using Python's strptime format codes. For example, '%Y-%m-%d' for ISO format dates like '2025-04-03'. Defaults to '%Y-%m-%d'.",
                }
            }
        },
        "required": ["datetime_str"]
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
        # Force one tool call at a time so the model must wait for a real
        # result (e.g. the current datetime) before using it as an input
        # to another tool, instead of nesting an unresolved call inline.
        params["parallel_tool_calls"] = False

    return client.chat.completions.create(**params)


def run_tool(tool_name, tool_args):
    if tool_name == "get_current_datetime":
        return get_current_datetime(**tool_args)
    elif tool_name == "add_duration_to_datetime":
        return add_duration_to_datetime(**tool_args)
    elif tool_name == "set_reminder":
        return set_reminder(**tool_args)
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
            messages, tools=[
                get_current_datetime_schema,
                add_duration_to_datetime_schema
            ])

        add_assistant_message(messages, response)

        if response.choices[0].finish_reason != "tool_calls":
            break

        tool_results = run_tools(response)

        messages.extend(tool_results)

    return messages


messages = run_conversations([
    {
        "role": "user",
        "content": "What is the date and time after 2 weeks and 30 minutes from now in '%Y-%m-%d %H:%M' format?"
    }
])

print("Final conversation history:")
for message in messages:
    print(f"{message['role']}: {message['content']}")

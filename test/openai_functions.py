import json
from timeit import timeit
from openai import AsyncClient, AsyncStream
from dotenv import load_dotenv
import os
import asyncio

from prompt_gen import Format, Model, Persona, PromptGenerator

load_dotenv("../.env")

client = AsyncClient(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

tools = []
tools.append(
    {
        "type": "function",
        "function": {
            "name": "get_column_headers",
            "description": "Get the column headers for the table.",
            "parameters": {},
        },
    }
)
tools.append(
    {
        "type": "function",
        "function": {
            "name": "get_column_headers_details",
            "description": "Get the details for a specific column header.",
            "parameters": {
                "type": "object",
                "properties": {
                    "header": {
                        "type": "string",
                        "description": "The column header to get details for.",
                    }
                },
                "required": ["header"],
            },
        },
    }
)
tools.append(
    {
        "type": "function",
        "function": {
            "name": "get_column_headers_details_length",
            "description": "Get the length of the details for a specific column header.",
            "parameters": {
                "type": "object",
                "properties": {
                    "details": {
                        "type": "string",
                        "description": "The details of an header, to get the length of.",
                    }
                },
                "required": ["details"],
            },
        },
    }
)


def get_column_headers():
    return [
        "Capital",
        "Country",
    ]


def get_column_headers_details(header: str):
    if header == "Capital":
        return "The capital of the United States is Washington, D.C."
    elif header == "Country":
        return "The United States is a country in North America."


def get_column_headers_details_length(details: str):
    return len(details)


def handle_tool_call(tool_call):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    print(name, args)
    if name == "get_column_headers":
        return get_column_headers()
    elif name == "get_column_headers_details":
        return get_column_headers_details(args.get("header"))
    elif name == "get_column_headers_details_length":
        return get_column_headers_details_length(args.get("details"))


async def run_prompt(messages):
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        tools=tools,
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        messages.append(response_message)
        for tool_call in tool_calls:
            tool_response = handle_tool_call(tool_call)
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": json.dumps(tool_response),
                }
            )
        return await run_prompt(messages)
    else:
        return response_message.content


async def main():
    messages = []
    messages.append(
        {
            "role": "user",
            "content": "What are the column headers and their details and their length?",
        }
    )

    response = await run_prompt(messages)
    print(response)


def run():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()


print(timeit(run, number=1))

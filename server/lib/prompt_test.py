import json
from openai import AsyncClient, AsyncStream
from dotenv import load_dotenv
import os

from prompt import PromptGenerator

load_dotenv("../../.env")
api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    raise ValueError("API key not found")

# client = AsyncClient(
#     api_key=api_key,
# )


def get_r_squared():
    return 187


stream = PromptGenerator(
    "Get the r squared value",
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_r_squared",
                "description": "Get the r-squared value for a linear regression model.",
                "parameters": {},
            },
        }
    ],
    functions={"get_r_squared": get_r_squared},
).run(api_key)

message = ""
for chunk in stream:
    if chunk["type"] == "ai_response":
        if not chunk["content"]:
            print("No content")
            continue
        message += chunk["content"]
    elif chunk["type"] == "tool_call":
        print("Tool call: ", chunk["name"], json.dumps(chunk["args"]))
    print(message)

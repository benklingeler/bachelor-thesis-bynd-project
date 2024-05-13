import base64
import json
import os
import sqlite3
import time
from fastapi import WebSocket
from openai import AsyncStream
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")
import uuid

from lib.prompt import AnswerStyle, Format, Model, Persona, PromptGenerator

chats = {}


def get_bynd_color(index):
    colors = ["#5B7F9E", "#A5C2E8", "#EBDC03", "#F69B00", "#AAC001"]
    return colors[index % len(colors)]


def get_dataset_columns(chatId):
    db = sqlite3.connect("db.sqlite3")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (int(chatId),))

    row = cursor.fetchone()

    results = json.loads(row[3])

    columns = results["data"].keys()
    print(columns)

    return columns


def scatter_plot_bytes(chatId, x_column, y_column, color="#6da7cd"):

    db = sqlite3.connect("db.sqlite3")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (int(chatId),))

    row = cursor.fetchone()

    results = json.loads(row[3])

    image_id = uuid.uuid4().hex

    x = results["data"][x_column]
    y = results["data"][y_column]

    plt.clf()
    plt.scatter(x, y, color=color)
    plt.xlabel(x_column)
    plt.ylabel(y_column)

    plt.savefig(f"./static/{image_id}.png", dpi=600)

    return f"""<a href="http://localhost:8000/static/{image_id}.png" target="_blank"><img src="http://localhost:8000/static/{image_id}.png" width="100%" /></a>"""


def get_quick_actions(api_key: str, response_message: str):

    response = PromptGenerator(
        f"""
            Generate between 1 and 3 Quick actions {{"label": "", "prompt": ""}} based on the response message: "{response_message}".
            
            - label: Quick summary of the underlaying prompt or message. About 1-5 words.
            - prompt:
                A prompt, that can be used by the users to further interact with the chat.
                Should contain a question or a call to action, that fits the previous response message of the model.
                Since the user sends the prompt back to the model, it should not adress the user directly.
                The prompt should be in the form of a question or a call to action, which could be asked by the user.
            
            Try to give the user a few options to choose from, so they can continue the conversation.
            Try to also give atleast one option that is not exactly related to the previous message, but still fits the context of the conversation.             
            Try to give one example to build on plot, if the message is about the dataset. The prompt could be similar to: "Build a plot with column on x and column on y"
        """,
        model=Model.GPT_4_TURBO,
        response_structure={"actions": [{"label": "", "prompt": ""}]},
        format=Format.JSON,
        plain=True,
    ).run(api_key=api_key)

    response_string = ""
    for chunk in response:
        if chunk["type"] == "ai_response" and chunk["content"] != None:
            response_string += chunk["content"]

    return json.loads(response_string)["actions"]


async def handleMessage(
    api_key: str, socket: WebSocket, message: str, user_profile: str
):

    if not socket.client or not socket.client.host:
        raise ValueError("Invalid socket client or host")

    if socket.client.host not in chats:
        raise ValueError("Chat not initialized")

    chatId = chats[socket.client.host]["chatId"]
    messages = chats[socket.client.host]["messages"]
    persona = Persona.NON_TECHNICAL

    # Function Wrapper
    def get_column_headers():
        return list(get_dataset_columns(chatId))

    def create_scatter_plot(x_column, y_column):
        return scatter_plot_bytes(chatId, x_column, y_column)

    if user_profile == "technical":
        persona = Persona.TECHNICAL
    elif user_profile == "business":
        persona = Persona.BUSINESS
    elif user_profile == "expert":
        persona = Persona.EXPERT

    response = PromptGenerator(
        prompt=message,
        persona=persona,
        format=Format.HTML,
        messages=messages,
        model=Model.GPT_4_TURBO,
        answerStyle=AnswerStyle.EXPLANATION,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_column_headers",
                    "description": "Get the column names of the dataset. Returns a list of strings. Usefull while explaining things about the dataset.",
                    "parameters": {},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_scatter_plot",
                    "description": "Create a scatter plot of the dataset. Returns an string with the HTML img tag wrapped in an a tag.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x_column": {
                                "type": "string",
                                "description": "The column (from the dataset) to use for the x-axis.",
                            },
                            "y_column": {
                                "type": "string",
                                "description": "The column (from the dataset) to use for the y-axis.",
                            },
                        },
                        "required": ["x_column", "y_column"],
                    },
                },
            },
        ],
        functions={
            "get_column_headers": get_column_headers,
            "create_scatter_plot": create_scatter_plot,
        },
    ).run(api_key)

    response_message = None
    for chunk in response:  # type: ignore
        if chunk["type"] == "ai_response":
            if chunk["content"] == None:
                break
            else:
                if not response_message:
                    response_message = chunk["content"]
                else:
                    response_message += chunk["content"]
                await socket.send_json(
                    {
                        "type": "message",
                        "message": response_message,
                        "isFinished": False,
                    }
                )
        elif chunk["type"] == "tool_call":
            await socket.send_json(
                {
                    "type": "tool_call",
                    "name": chunk["name"],
                    "args": json.dumps(chunk["args"]),
                }
            )

    await socket.send_json(
        {"type": "message", "message": response_message, "isFinished": True}
    )

    if response_message:
        await socket.send_json(
            {
                "type": "quick_actions",
                "loading": True,
            }
        )
        await socket.send_json(
            {
                "type": "quick_actions",
                "actions": get_quick_actions(api_key, response_message),
            }
        )

    messages.append({"role": "user", "content": message})
    messages.append({"role": "system", "content": response_message})
    chats[socket.client.host]["messages"] = messages


async def update_user_profile(socket: WebSocket, user_profile: str):
    if not socket.client or not socket.client.host:
        raise ValueError("Invalid socket client or host")

    current_chat = chats[socket.client.host]

    await init_chat(socket, current_chat["chatId"], user_profile)

    await socket.send_json(
        {"type": "user_profile_updated", "user_profile": user_profile}
    )


async def init_chat(socket: WebSocket, chatId: str, user_profile: str):
    db = sqlite3.connect("db.sqlite3")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (int(chatId),))

    row = cursor.fetchone()

    results = json.loads(row[3])

    initial_prompt = f"""
        The following results are information regarding the results of an linear regression model.
        
        results: {json.dumps(results['metrics'])}
        context of the results: {results['context']}
    """

    if not socket.client or not socket.client.host:
        raise ValueError("Invalid socket client or host")

    chats[socket.client.host] = {
        "chatId": chatId,
        "messages": [{"role": "user", "content": initial_prompt}],
        "user_profile": user_profile,
    }

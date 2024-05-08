import datetime
import json

from dotenv import load_dotenv
import os
from typing import Annotated, Optional, Union
from fastapi import FastAPI, Response, WebSocket, File, UploadFile, Form
import sqlite3
from fastapi.middleware.cors import CORSMiddleware
import openai

from lib.database_seed import seed
from lib.pdf_generator.generate import generate_pdf
import time

load_dotenv("../.env")

client = openai.Client(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
app = FastAPI()
sockets = []
chats = {}

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

seed()


async def send_response(socket: WebSocket, prompt: str):
    messages = chats[socket.client.host]
    messages.append({"role": "user", "content": prompt})

    stream = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        stream=True,
    )

    chunks = []

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            chunks.append(chunk.choices[0].delta.content)
            await socket.send_json({"message": "".join(chunks), "isFinished": False})

    await socket.send_json({"message": "".join(chunks), "isFinished": True})
    messages.append({"role": "system", "content": "".join(chunks)})
    chats[socket.client.host] = messages


async def initChat(socket, chatId):
    db = sqlite3.connect("db.sqlite3")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (int(chatId),))

    row = cursor.fetchone()

    results = json.loads(row[3])

    initial_prompt = f"""
      The following results are information regarding the results of an linear regression model.
      
      results: {json.dumps(results['metrics'])}
      context of the results: {results['context']}
      
      Explain the given results and context in a way that a non-technical person can understand it.
      Give the user a clear understand, what the models does, what factors are influencing the result and
      why the result may be interesting from a business perspective.
      
      Always follow the guidelines for the answers and the user information strictly!
      
      Information regarding your answer style:
        - Always focus on the business or marketing aspect and not the technical details.
        - Please use proper grammar.
        - Please be polite.
        - Please be concise.
        - Please be clear.
        - Please answer as simple as possible
        - Do not use any abbreviations.
        - Do not use any technical terms.
        - Keep your answer as short as possible!
        - Sturcture your answer for best readability with short sentencens
        - Explain your answer in a way that a non-technical person can understand it
        - Dont answer to questions that are not regarding the model.
        - Only refer to knowledge that is provided in the context. Do not make any assumptions.
        
      Information regarding the answer format:
        - Use html to style your answer
        - Keep the styling simple, but precise with an clear visual structure
        - Use lists if possible to structure your answer
        - Use highlight numbers. To highlight, wrap the text in a span with the class "highlight"
        - The background of the chat is dark, so use bright colors for text.
        
      
      Try to follow the following structure if you answer a question or explain something:
        - Start with a short introduction
        - Explain the main part
        - End with a conclusion
        - Give example questions, that the user may ask to get more information
      
      Information about the user, that is asking questions and that you are answering to:
        - The user is a non-technical person
        - The user is a business person
        - The user might have some marketing knowledge
        - The user is interested in the results of the model
        - The user is representing the company that the model was created for
        - Dont adress the user directly in your answers, always refer as "the company" or the company name if provided in the context
    """

    await send_response(
        socket,
        initial_prompt,
    )


async def answerMessage(socket, chatId, message):

    await send_response(
        socket,
        message,
    )


@app.get("/reports")
def get_reports():
    db = sqlite3.connect("db.sqlite3")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM reports")
    reports = cursor.fetchall()

    cursor.close()

    clean_reports = [
        {"id": report[0], "label": report[1], "created_at": report[4]}
        for report in reports
    ]

    return clean_reports


@app.get("/report/{label}")
def get_single_report_pdf(label: str):
    db = sqlite3.connect("db.sqlite3")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM reports WHERE label = ?", (label,))
    report = cursor.fetchone()

    cursor.close()

    if report is None:
        return {"error": "Report not found"}, 404

    filename = report[1].replace(" ", "_")
    quoted_filename = f'filename="{filename}.pdf"'

    # Return the pdf file with respective content type
    return Response(
        content=report[2],
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; {quoted_filename}"},
    )


@app.post("/upload")
async def upload_report(
    label: Annotated[str, Form()], file: Annotated[UploadFile, Form()]
):

    try:
        file_data = await file.read()
        results = json.loads(file_data.decode("utf-8"))
        filename = str(int(time.time()))

        generate_pdf(filename, results)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}, 500

    with open(f"{filename}.pdf", "rb") as file:
        pdf = file.read()

    # Remove pdf
    os.remove(f"{filename}.pdf")

    db = sqlite3.connect("db.sqlite3")

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO reports (label, pdf_file, results_json, created_at) VALUES (?, ?, ?, ?)",
        (label, pdf, json.dumps(results), datetime.datetime.now().isoformat()),
    )

    db.commit()
    cursor.close()

    return {"filename": file}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        json_data = json.loads(data)

        if "chatId" in json_data and "message" not in json_data:
            chats[websocket.client.host] = []
            sockets.append({"chatId": json_data["chatId"], "socket": websocket})
            await initChat(websocket, json_data["chatId"])

        if "chatId" in json_data and "message" in json_data:
            sockets.append({"chatId": json_data["chatId"], "socket": websocket})
            await answerMessage(websocket, json_data["chatId"], json_data["message"])

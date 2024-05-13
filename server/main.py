import datetime
import json

from dotenv import load_dotenv
import os
from typing import Annotated, Optional, Union
from fastapi import FastAPI, Response, WebSocket, File, UploadFile, Form
import sqlite3
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import openai

from lib.database_seed import seed
from lib.pdf_generator.generate import generate_pdf
import time

from lib.chat import handleMessage, init_chat, update_user_profile

load_dotenv("../.env")

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key not found")

client = openai.Client(
    api_key=api_key,
)
app = FastAPI()

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

app.mount("/static", StaticFiles(directory="static"), name="static")


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

    with open(f"{filename}.pdf", "rb") as pdf_file:
        pdf = pdf_file.read()

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

        if "type" not in json_data:
            continue

        if json_data["type"] == "initChat":
            await init_chat(websocket, json_data["chatId"], json_data["user_profile"])

        if json_data["type"] == "update_user_profile":
            await update_user_profile(websocket, json_data["user_profile"])

        if json_data["type"] == "message":
            await handleMessage(
                api_key, websocket, json_data["message"], json_data["user_profile"]
            )

from sqlite3 import Connection
import sqlite3


def seed():
    db = sqlite3.connect("db.sqlite3")

    cursor = db.cursor()
    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS reports (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              label TEXT NOT NULL,
              pdf_file BLOB NOT NULL,
              results_json TEXT NOT NULL  
            )
        """
    )

    db.commit()
    cursor.close()

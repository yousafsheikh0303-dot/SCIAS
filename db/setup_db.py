import sqlite3
import os

os.makedirs("db", exist_ok=True)

def init_db():
    conn = sqlite3.connect("db/scias.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            message TEXT,
            agent_used TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mandi_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop TEXT,
            price REAL,
            market TEXT,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized at db/scias.db")

if __name__ == "__main__":
    init_db()
import sqlite3


def create_table_if_not_exists():
    try:
        cursor.execute("""CREATE TABLE IF NOT EXISTS queues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100),
            chat_id INTEGER,
            queue TEXT
        )""")
    except sqlite3.DatabaseError as err:
        print(f"Error: {err}")
    else:
        conn.commit()


def insert(name: str, chat_id: int, queue: list):
    try:
        cursor.execute("""INSERT INTO queues (name, chat_id, queue)
                        VALUES (?, ?, ?)""", (name, chat_id, str(queue)))
    except sqlite3.DatabaseError as err:
        print(f"Error: {err}")
    else:
        conn.commit()

def remove(name: str):
    try:
        cursor.execute("""DELETE FROM queues WHERE name = ?""", (name,))
    except sqlite3.DatabaseError as err:
        print(f"Error: {err}")
    else:
        conn.commit()

def clean_table():
    try:
        cursor.execute("""DELETE FROM queues""")
    except sqlite3.DatabaseError as err:
        print(f"Error: {err}")
    else:
        conn.commit()


if __name__ == "__main__":
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    create_table_if_not_exists()

    
    conn.close()

import sqlite3
from config import STORAGE_NAME
import ast


class QueueNotFoundException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'QueueNotFoundException: {self.message}'
        else:
            return 'QueueNotFoundException has not been raised'


def create_table_if_not_exists():
    try:
        cursor.execute("""CREATE TABLE IF NOT EXISTS queues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            queue_id INTEGER,
            name VARCHAR(100) COLLATE NOCASE,
            queue TEXT
        )""")
    except sqlite3.DatabaseError as err:
        raise err
    else:
        conn.commit()


def name_exists_in_chat(name: str, chat_id: int):
    conn = sqlite3.connect(STORAGE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""SELECT * FROM queues
            WHERE (name = ? and chat_id = ?)
            COLLATE NOCASE
        """, (name, chat_id))

        result = cursor.fetchone()

        return bool(result)
    except sqlite3.DatabaseError as err:
        raise err

    conn.close()


def queue_id_exists_in_chat(chat_id: int, queue_id: int):
    conn = sqlite3.connect(STORAGE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""SELECT * FROM queues
            WHERE (queue_id = ? and chat_id = ?)
        """, (queue_id, chat_id))

        result = cursor.fetchone()

        return bool(result)
    except sqlite3.DatabaseError as err:
        raise err

    conn.close()


def user_exists_in_queue(chat_id: int, queue_id: int, user_id: int):
    conn = sqlite3.connect(STORAGE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """SELECT queue FROM queues
            WHERE (queue_id = ? and chat_id = ?)
            """,
            (queue_id, chat_id)
        )

        result = cursor.fetchone()[0]
        queue = ast.literal_eval(result)

        return user_id in queue
    except sqlite3.DatabaseError as err:
        raise err

    conn.close()


def add_queue(chat_id: int, queue_id: int, name: str, queue: list):
    conn = sqlite3.connect(STORAGE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """INSERT INTO queues (chat_id, queue_id, name, queue)
            VALUES (?, ?, ?, ?)""",
            (chat_id, queue_id, name, str(queue))
        )
    except sqlite3.DatabaseError as err:
        raise err
    else:
        conn.commit()

    conn.close()


def get_queue(chat_id: int, queue_id: int):
    conn = sqlite3.connect(STORAGE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """SELECT name, queue FROM queues
            WHERE (chat_id = ? and queue_id = ?)
            """,
            (chat_id, queue_id)
        )
        result = list(cursor.fetchone())
        result[1] = ast.literal_eval(result[1])

        return result
    except sqlite3.DatabaseError as err:
        raise err
    else:
        conn.commit()

    conn.close()

def get_queue_id_by_name(chat_id: int, name: str):
    conn = sqlite3.connect(STORAGE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """SELECT queue_id FROM queues
            WHERE (chat_id = ? and name = ?)
            """,
            (chat_id, name)
        )

        result = int(cursor.fetchone()[0])

        return result
    except sqlite3.DatabaseError as err:
        raise err
    else:
        conn.commit()

    conn.close()


def delete_queue(chat_id: int, name: str):
    conn = sqlite3.connect(STORAGE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """DELETE FROM queues 
            WHERE (chat_id = ? and name = ?)""", (chat_id, name)
        )
    except sqlite3.DatabaseError as err:
        raise err
    else:
        conn.commit()

    conn.close()


def clean_table():
    conn = sqlite3.connect(STORAGE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""DELETE FROM queues""")
    except sqlite3.DatabaseError as err:
        raise err
    else:
        conn.commit()

    conn.close()


def add_to_queue(chat_id: int, queue_id: int, new_member: int):
    conn = sqlite3.connect(STORAGE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """SELECT queue FROM queues
            WHERE (chat_id = ? and queue_id = ?)
            """,
            (chat_id, queue_id)
        )

        result = cursor.fetchone()[0]
        updated_queue = ast.literal_eval(result)
        updated_queue.append(new_member)

        cursor.execute(
            """UPDATE queues
            SET queue = ?
            WHERE (chat_id = ? and queue_id = ?)""",
            (str(updated_queue), chat_id, queue_id)
        )
    except sqlite3.DatabaseError as err:
        raise err
    else:
        conn.commit()

    conn.close()


def remove_from_queue(chat_id: int, queue_id: int, new_member: int):
    conn = sqlite3.connect(STORAGE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """SELECT queue FROM queues
            WHERE (chat_id = ? and queue_id = ?)
            """,
            (chat_id, queue_id)
        )

        result = cursor.fetchone()[0]
        updated_queue = ast.literal_eval(result)
        updated_queue.remove(new_member)

        cursor.execute(
            """UPDATE queues
            SET queue = ?
            WHERE (chat_id = ? and queue_id = ?)""",
            (str(updated_queue), chat_id, queue_id)
        )
    except sqlite3.DatabaseError as err:
        raise err
    else:
        conn.commit()

    conn.close()


if __name__ == "__main__":
    conn = sqlite3.connect(STORAGE_NAME)
    cursor = conn.cursor()

    create_table_if_not_exists()

    conn.close()

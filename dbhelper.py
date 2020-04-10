from peewee import *

from models import Chat, Queue


def add_chat(chat_id, language="en"):
    chat_exists = Chat.select().where(
        Chat.chat_id == chat_id
    ).exists()

    if chat_exists:
        return False

    new_chat = Chat(
        chat_id=chat_id,
        language=language
    )
    new_chat.save()
    return True


def del_chat(chat_id):
    try:
        chat = Chat.get(Chat.chat_id == chat_id)
        chat.delete_instance()
        return True
    except DoesNotExist:
        return False


def add_queue(chat_id, name):
    queue_in_chat_exists = Queue.select().where(
        Queue.name == name,
        Queue.chat_id == chat_id
    ).exists()

    if queue_in_chat_exists:
        return False

    row = Queue(
        name=name,
        chat_id=chat_id,
        text_represenation="some text"
    )
    row.save()


def del_queue(chat_id, name):
    try:
        queue = Queue.select().where(
            Queue.queue_name == name,
            Queue.chat_id == chat_id
        ).get()
        queue.delete_instance()
    except DoesNotExist:
        return False


def get_lang(chat_id):
    return Chat.get(Chat.chat_id == chat_id).language

import logging

import telebot
from telebot import types

import dbhelper
from config import API_TOKEN

bot = telebot.TeleBot(API_TOKEN)

# DEBUG
# telebot.logger.setLevel(logging.DEBUG)


def queue_markup():
    markup = types.InlineKeyboardMarkup()

    enter_queue_button = types.InlineKeyboardButton(
        "Enter the queue", callback_data="cb_enter")
    leave_queue_button = types.InlineKeyboardButton(
        "Leave the queue", callback_data="cb_leave")
    markup.row(enter_queue_button, leave_queue_button)

    return markup


def enter_queue(chat_id: int, queue_id: int, user_id: int) -> bool:
    if not dbhelper.queue_id_exists_in_chat(chat_id, queue_id):
        raise dbhelper.QueueNotFoundException

    if not dbhelper.user_exists_in_queue(chat_id, queue_id, user_id):
        dbhelper.add_to_queue(chat_id, queue_id, user_id)
        return True
    else:
        return False


def left_queue(chat_id: int, queue_id: int, user_id: int) -> bool:
    if not dbhelper.queue_id_exists_in_chat(chat_id, queue_id):
        raise dbhelper.QueueNotFoundException

    if dbhelper.user_exists_in_queue(chat_id, queue_id, user_id):
        dbhelper.remove_from_queue(chat_id, queue_id, user_id)
        return True
    else:
        return False


def queue_output(chat_id: int, queue: list) -> str:
    def user_output(user):
        return f"[{user.first_name} {user.last_name}](tg://user?id={user.id})"

    user_list = [bot.get_chat_member(
        chat_id, user_id).user for user_id in queue]

    return '\n'.join([f"{pos[0]+1}. {user_output(pos[1])}" for pos in enumerate(user_list)])


@bot.message_handler(commands=["start"], func=lambda message: message.chat.type == "private")
def command_start_private_chat(message):
    response_text = "Hi! I can only work in groups. Please, add me to the group chat, that needs"
    " a hero of queues!"
    bot.send_message(message.chat.id, response_text)


@bot.message_handler(commands=["start"], func=lambda message: message.chat.type == "group")
def command_start(message):
    bot.send_message(
        message.chat.id,
        "Hi! I can create queues!"
    )


@bot.message_handler(commands=["create"], func=lambda message: message.chat.type == "group")
def command_create(message):
    command_split = message.text.split(maxsplit=1)

    if len(command_split) != 2:
        response_text = "You should use the 'create' command correctly:\n\t/create QUEUE_NAME"
        bot.send_message(message.chat.id, response_text)
        return

    if dbhelper.count_queue_in_chat(message.chat.id) > 5:
        response_text = "Chat queue limit reached! Please, delete unnecessary queues or use existing ones"
        bot.send_message(message.chat.id, response_text)
        return

    name = command_split[1]

    if dbhelper.name_exists_in_chat(name, message.chat.id):
        response_text = f'Sorry, but the queue with the name "{name}" already exists'
        bot.send_message(message.chat.id, response_text)
        return

    response_text = f"Queue: {name}\nNumber of members: 0\nMembers:\n"
    message_id = bot.send_message(message.chat.id, response_text,
                                  reply_markup=queue_markup()).message_id

    dbhelper.add_queue(message.chat.id, message_id, name, [])


@bot.message_handler(commands=["delete"], func=lambda message: message.chat.type == "group")
def command_delete(message):
    command_split = message.text.split(maxsplit=1)

    if len(command_split) != 2:
        response_text = f"You should use the 'delete' command correctly:\n\t/delete QUEUE_NAME"
        bot.send_message(message.chat.id, response_text)
        return

    name = command_split[1]

    if not dbhelper.name_exists_in_chat(name, message.chat.id):
        response_text = f"Sorry, but the queue with the name '{name}' does not exist"
        bot.send_message(message.chat.id, response_text)
        return

    queue_id = dbhelper.get_queue_id_by_name(message.chat.id, name)
    dbhelper.delete_queue(message.chat.id, name)
    bot.edit_message_reply_markup(message.chat.id, queue_id)

    response_text = f"Queue '{name}' was successfully deleted"
    bot.send_message(message.chat.id, response_text)


@bot.callback_query_handler(func=lambda call: call.message.chat.type == "group")
def callback_query(call):
    call_id = call.id
    chat_id = call.message.chat.id
    queue_id = call.message.message_id
    user_id = call.from_user.id

    if call.data == "cb_enter":
        try:
            is_queue_entered = enter_queue(chat_id, queue_id, user_id)
        except dbhelper.QueueNotFoundException:
            bot.answer_callback_query(
                call_id, "Queue does not exist! Please contact your chat administrator!")
            return

        if is_queue_entered:
            name, queue = dbhelper.get_queue(chat_id, queue_id)

            edited_text = f"Queue: {name}\nNumber of members: {len(queue)}\nMembers:\n{queue_output(chat_id, queue)}"
            bot.edit_message_text(
                edited_text,
                chat_id,
                queue_id,
                reply_markup=queue_markup(),
                parse_mode="markdown"
            )
            bot.answer_callback_query(call.id)
        else:
            bot.answer_callback_query(
                call_id,
                "You are already in this queue!"
            )
    elif call.data == "cb_leave":
        try:
            is_queue_left = left_queue(chat_id, queue_id, user_id)
        except dbhelper.QueueNotFoundException:
            bot.answer_callback_query(
                call_id,
                "Queue does not exist! Please contact your chat administrator!"
            )
            return

        if is_queue_left:
            name, queue = dbhelper.get_queue(chat_id, queue_id)

            edited_text = f"Queue: {name}\nNumber of members: {len(queue)}\nMembers:\n{queue_output(chat_id, queue)}"
            bot.edit_message_text(
                edited_text,
                chat_id,
                queue_id,
                reply_markup=queue_markup(),
                parse_mode="markdown"
            )
            bot.answer_callback_query(call.id)
        else:
            bot.answer_callback_query(
                call_id, "You are not in this queue yet!")
    else:
        bot.answer_callback_query(call_id, "Something went wrong...")


if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)

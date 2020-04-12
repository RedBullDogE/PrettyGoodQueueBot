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


@bot.message_handler(commands=["start"], func=lambda message: message.chat.type == "private")
def command_start_private_chat(message):
    bot.send_message(message.chat.id, "Hi! I can only work in groups. Please, add me to the group chat, that needs"
                                      " a hero of queues!")


@bot.message_handler(commands=["start"], func=lambda message: message.chat.type == "group")
def command_start(message):
    bot.send_message(
        message.chat.id,
        "Hi! I can create queues!"
    )


@bot.message_handler(commands=["create"], func=lambda message: message.chat.type == "group")
def command_create(message):
    name = message.text.split()[1]

    if dbhelper.name_exists_in_chat(name, message.chat.id):
        response_text = f'Sorry, but the queue with the name "{name}" already exists'
        bot.send_message(message.chat.id, response_text)
        return


    response_text = f"Queue: {name}\nNumber of members: 0\nMembers:\n"
    message_id = bot.send_message(message.chat.id, response_text,
                     reply_markup=queue_markup()).message_id
    dbhelper.insert(message.chat.id, message_id, name, [])


def enter_queue(chat_id, queue_id, user_id):
    if dbhelper.queue_id_exists_in_chat(chat_id, queue_id) and not dbhelper.user_exists_in_queue(chat_id, queue_id, user_id):
        dbhelper.add_to_queue(chat_id, queue_id, user_id)
        return True
    else:
        return False


def left_queue(chat_id, queue_id, user_id):
    if dbhelper.queue_id_exists_in_chat(chat_id, queue_id) and dbhelper.user_exists_in_queue(chat_id, queue_id, user_id):
        dbhelper.remove_from_queue(chat_id, queue_id, user_id)
        return True
    else:
        return False


@bot.callback_query_handler(func=lambda call: call.message.chat.type == "group")
def callback_query(call):
    if call.data == "cb_enter":
        if enter_queue(call.message.chat.id, call.message.message_id, call.message.from_user.id):
            name, queue = dbhelper.get_queue(call.message.chat.id, call.message.message_id)
            edited_text = f"Queue: {name}\nNumber of members: {len(queue)}\nMembers: {queue}"
            bot.edit_message_text(edited_text, call.message.chat.id, call.message.message_id, reply_markup=queue_markup())
            # bot.answer_callback_query(call.id, 'Done!')
        else:
            bot.answer_callback_query(call.id, "User is already in the queue!")
    elif call.data == "cb_leave":
        if left_queue(call.message.chat.id, call.message.message_id, call.message.from_user.id):
            name, queue = dbhelper.get_queue(call.message.chat.id, call.message.message_id)
            edited_text = f"Queue: {name}\nNumber of members: {len(queue)}\nMembers: {queue}"
            bot.edit_message_text(edited_text, call.message.chat.id, call.message.message_id, reply_markup=queue_markup())
        else:
            bot.answer_callback_query(call.id, "User in not in this queue yet!")
    else:
        bot.answer_callback_query(call.id, "Something went wrong...")


if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)

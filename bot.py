import logging
from datetime import datetime

import telebot
from telebot import types

import dbhelper
from bothelper import *
from config import API_TOKEN
from localization import langs

bot = telebot.TeleBot(API_TOKEN)
telebot.logger.setLevel(logging.DEBUG)


# TODO /setcommands in telegram FatherBot:
#   -/help
#   -/menu
#   -...

# TODO
#   - admin menu
#   - main menu
def gen_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)

    create_button = types.InlineKeyboardButton("Create new queue", callback_data=f"cb_create")
    help_button = types.InlineKeyboardButton("Help", callback_data=f"cb_help")
    markup.add(create_button, help_button)

    return markup


def gen_queue_markup():
    markup = types.InlineKeyboardMarkup()

    enter_queue_button = types.InlineKeyboardButton("Enter the queue", callback_data=f"cb_enter")
    leave_queue_button = types.InlineKeyboardButton("Leave the queue", callback_data=f"cb_leave")
    markup.row(enter_queue_button, leave_queue_button)
    markup.row_width = 10
    enter_button_list = [types.InlineKeyboardButton(f"{i}", callback_data=f"cb_get_{i}")
                         for i in range(1, 31)]
    for i in range(len(enter_button_list) // 8 + 1):
        markup.row(*enter_button_list[8 * i:8 * (i + 1)])
    return markup


@bot.message_handler(commands=["start"], func=lambda message: message.chat.type == "private")
def command_start_private_chat(message):
    bot.send_message(message.chat.id, "Hi! I can only work in groups. Please, add me to the group chat, that needs"
                                      " a hero of queues!")


@bot.message_handler(commands=["start"], func=lambda message: message.chat.type == "group")
def command_start(message):
    dbhelper.add_chat(message.chat.id)
    bot.send_message(
        message.chat.id,
        langs[dbhelper.get_lang(message.chat.id)]["start_message"]
    )


@bot.message_handler(commands=["menu"], func=lambda message: message.chat.type == "group")
def command_menu(message):
    bot.send_message(
        message.chat.id,
        langs[dbhelper.get_lang(message.chat.id)]["menu_message"],
        reply_markup=gen_menu_markup())


@bot.message_handler(commands=["create"], func=lambda message: message.chat.type == "group")
def command_create(call):
    msg = bot.reply_to(
        call.message,
        langs[dbhelper.get_lang(call.message.chat.id)]["create_message_1"])
    bot.register_next_step_handler(msg, create_step_name)
    bot.answer_callback_query(call.id)


def create_step_choose(message):
    pass


def create_step_name(message):
    queue_name = message.text.strip()
    current_time = datetime.strftime(datetime.now(), '%d/%m/%Y')
    answer_text = langs[dbhelper.get_lang(message.chat.id)]["create_message_2"].format(queue_name, current_time)
    bot.send_message(message.chat.id, answer_text, reply_markup=gen_queue_markup())


def enter_queue(call, username, number_in_queue):
    message = call.message

    if username is None:
        username = call.from_user.id

    if is_busy(message.text, number_in_queue):
        bot.answer_callback_query(call.id, "This place in the queue is already taken")
        return call.message.html_text
    elif is_in_line(message.html_text, username):
        text_after_leaving = left_queue(call, username)
        header = "\n".join(text_after_leaving.split("\n")[:2])
        user_list = text_after_leaving.split("\n")[2:]
        user_list.append(f"{number_in_queue}. {username_format(call.from_user)}")
        user_list_text = "\n".join(sorted(user_list, key=lambda user_info: int(user_info.split(".")[0])))
        new_text = f"{header}\n{user_list_text}"
        bot.edit_message_text(new_text, message.chat.id, message.message_id, reply_markup=gen_queue_markup(),
                              parse_mode="html")
        bot.answer_callback_query(call.id, f"Changing place to {number_in_queue}...")
    else:
        header = "\n".join(message.text.split("\n")[:2])
        user_list = message.html_text.split("\n")[2:]
        user_list.append(f"{number_in_queue}. {username_format(call.from_user)}")
        user_list_text = "\n".join(sorted(user_list, key=lambda user_info: int(user_info.split(".")[0])))
        new_text = f"{header}\n{user_list_text}"
        bot.edit_message_text(new_text, message.chat.id, message.message_id, reply_markup=gen_queue_markup(),
                              parse_mode="html")
        bot.answer_callback_query(call.id, f"You ranked {number_in_queue} in line")


def left_queue(call, username):
    if username is None:
        username = call.from_user.id

    if is_in_line(call.message.html_text, username):
        header = "\n".join(call.message.text.split("\n")[:2])
        queue_line_list = call.message.html_text.split("\n")[2:]
        username_list = [line.split(" ", 1)[-1].split("@")[-1] for line in queue_line_list]
        username_and_id_list = [extract_user_id(us)[0] if any(extract_user_id(us)) else us for us in username_list]

        for i in range(len(username_and_id_list)):
            if username_and_id_list[i] == str(username):
                queue_line_list.pop(i)
                break
        user_list_text = "\n".join(queue_line_list)
        new_text = f"{header}\n{user_list_text}"

        try:
            bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id,
                                  reply_markup=gen_queue_markup(), parse_mode="html")
        except telebot.apihelper.ApiException:
            bot.answer_callback_query(call.id, "Something went wrong...")

        return new_text
    else:
        bot.answer_callback_query(call.id, "You are not in the queue yet")
        return call.message.html_text


@bot.callback_query_handler(func=lambda call: call.message.chat.type == "group")
def callback_query(call):
    if call.data == "cb_create":
        command_create(call)
    elif call.data == "cb_enter":
        free_place = find_free_place(call.message.text)
        if free_place == -1:
            bot.answer_callback_query(call.id, "There are no free places in this queue")
            return
        enter_queue(call, call.from_user.username, free_place)
    elif call.data == "cb_leave":
        left_queue(call, call.from_user.username)
    elif call.data == "cb_help":
        bot.answer_callback_query(call.id, "help...")
    elif call.data.split("_")[-1].isdigit():
        number_in_queue = int(call.data.split("_")[-1])
        enter_queue(call, call.from_user.username, number_in_queue)
    else:
        bot.answer_callback_query(call.id, "Something went wrong...")


if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)

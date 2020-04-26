# -*- coding: utf-8 -*-

import telebot
from telebot import types
import flask

import time

import dbhelper
import config


bot = telebot.TeleBot(config.API_TOKEN)

DEBUG_WITH_POLLING = True


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

    return '\n'.join([f"{pos[0]}. {user_output(pos[1])}" for pos in enumerate(user_list, start=1)])


def is_admin(chat_id: int, user_id: int) -> bool:
    admins = list(map(lambda member: member.user.id,
                      bot.get_chat_administrators(chat_id)))
    member = bot.get_chat_member(chat_id, user_id).user.id

    return member in admins


@bot.message_handler(commands=["start", "help"], func=lambda message: message.chat.type == "private")
def command_start_private_chat(message):
    response_text = "Hi! I can only work in groups." \
        "\nPlease, add me to the group chat, that needs a hero of queues😎"

    bot.send_message(message.chat.id, response_text)


@bot.message_handler(commands=["start"], func=lambda message: message.chat.type == "group")
def command_start(message):
    response_text = "Hi! I can create queues! Let's try to do this!🤗" \
        "\nType /create QUEUE_NAME to create a new queue or " \
        "use /help to view all available commands!"

    bot.send_message(message.chat.id, response_text)


@bot.message_handler(commands=["help"], func=lambda message: message.chat.type == "group")
def command_start(message):
    response_text = "List of available commands 🧐:" \
        "\n\n▪️ /create QUEUE_NAME — create a new queue, ONLY FOR ADMINS" \
        "\n▪️ /delete or /remove QUEUE_NAME — stop (delete) specified queue, ONLY FOR ADMINS" \
        "\n▪️ /list — display all working queues of your chat" \
        "\n▪️ /find QUEUE_NAME — find existing queue in chat (if you lost it)" \
        "\n\nIn this chat you can carry out 6 queues at the same time. " \
        "To check the total number of queues use the /list command." \
        "\n\nAlso, if you find a bug or you have some questions write here: @redbulldog"

    bot.send_message(message.chat.id, response_text)


@bot.message_handler(
    commands=["create"],
    func=lambda message: message.chat.type == "group" and
    is_admin(message.chat.id, message.from_user.id)
)
def command_create(message):
    command_split = message.text.split(maxsplit=1)

    if len(command_split) != 2:
        response_text = "You should use the 'create' command correctly😓:\n\t/create QUEUE_NAME"
        bot.send_message(message.chat.id, response_text)
        return

    if dbhelper.count_queue_in_chat(message.chat.id) > 5:
        response_text = "Chat queue limit reached!😩" \
            "\nPlease, delete unnecessary queues or use existing ones"
        bot.send_message(message.chat.id, response_text)
        return

    name = command_split[1]

    if dbhelper.name_exists_in_chat(name, message.chat.id):
        response_text = f"Sorry, but the queue with the name '{name}' already exists😰"
        bot.send_message(message.chat.id, response_text)
        return

    response_text = "🔴🔴🔴\n" \
        f"\nQueue: {name}" \
        "\nNumber of members: 0" \
        "\nStatus: ✅\n" \
        "\nMembers:\n"
    message_id = bot.send_message(message.chat.id, response_text,
                                  reply_markup=queue_markup()).message_id

    dbhelper.add_queue(message.chat.id, message_id, name, [])


@bot.message_handler(
    commands=["delete", "remove"],
    func=lambda message: message.chat.type == "group" and
    is_admin(message.chat.id, message.from_user.id)
)
def command_delete(message):
    command_split = message.text.split(maxsplit=1)

    if len(command_split) != 2:
        response_text = f"You should use the '{command_split[0][1:]}' command correctly😓:" \
            f"\n\t{command_split[0]} QUEUE_NAME"

        bot.send_message(message.chat.id, response_text)
        return

    name = command_split[1]

    if not dbhelper.name_exists_in_chat(name, message.chat.id):
        response_text = f"Sorry, but the queue with the name '{name}' does not exist☹️"
        bot.send_message(message.chat.id, response_text)
        return

    queue_id = dbhelper.get_queue_id_by_name(message.chat.id, name)
    dbhelper.delete_queue(message.chat.id, name)
    queue_message = bot.edit_message_reply_markup(message.chat.id, queue_id)
    edited_text = queue_message.text.replace("✅", "❌")
    bot.edit_message_text(edited_text, queue_message.chat.id, queue_id)


    response_text = f"Queue '{name}' was successfully deleted😋"
    bot.send_message(message.chat.id, response_text)


@bot.message_handler(
    commands=["deleteall", "removeall"],
    func=lambda message: message.chat.type == "group" and
    is_admin(message.chat.id, message.from_user.id)
)
def command_deleteall(message):
    if dbhelper.count_queue_in_chat(message.chat.id) == 0:
        response_text = "Oh, there are no queues in this chat😕"
        bot.send_message(message.chat.id, response_text)
        return
    
    response_text = "Are you sure you want to delete all queues in this group? Yes/No"
    msg = bot.reply_to(message, response_text)
    bot.register_next_step_handler(msg, deleteall_queues)


def deleteall_queues(message):
    try:
        if message.text.lower().strip() in ["yes", "y", "ye", "yep"]:
            queue_id_list = dbhelper.delete_all_queues(message.chat.id)
            for qid in queue_id_list:
                bot.edit_message_reply_markup(message.chat.id, qid)

            response_text = "All queues was successfully deleted💀💀💀"
            bot.send_message(message.chat.id, response_text)
        elif message.text.lower().strip() in ["no", "n", "nope"]:
            response_text = "Well, finish it😐"
            bot.send_message(message.chat.id, response_text)
        else:
            response_text = "I don't understand😰 Please, answer YES or NO😣"
            msg = bot.reply_to(message, response_text)
            bot.register_next_step_handler(msg, deleteall_queues)

    except Exception as e:
        bot.reply_to(message, "Oooops🥴🥴🥴 Please, contact your chat administrator")


@bot.message_handler(commands=["list"], func=lambda message: message.chat.type == "group")
def command_list(message):
    queue_list = dbhelper.get_all_queue_names(message.chat.id)

    if queue_list:
        queues = "\n\t".join(
            [f"{el[0]}. {el[1]}" for el in enumerate(queue_list, start=1)])

        response_text = "All available queues in your chat:" \
            f"\n\t{queues}" \
            f"\nFullness: {len(queue_list)}/6"

        bot.send_message(message.chat.id, response_text)
    else:
        response_text = "There are no queues in this chat yet! Maybe let's create?😏"
        bot.send_message(message.chat.id, response_text)


@bot.message_handler(commands=["find"], func=lambda message: message.chat.type == "group")
def command_list(message):
    command_split = message.text.split(maxsplit=1)

    if len(command_split) != 2:
        response_text = f"You should use the 'find' command correctly😓:" \
            f"\n\t/find QUEUE_NAME"

        bot.send_message(message.chat.id, response_text)
        return

    name = command_split[1]

    if not dbhelper.name_exists_in_chat(name, message.chat.id):
        response_text = f"Sorry, I can't find the queue with the name '{name}'☹️"
        bot.send_message(message.chat.id, response_text)
        return

    message_id = dbhelper.get_queue_id_by_name(message.chat.id, name)
    message.message_id = message_id

    response_text = "I found!😇"
    bot.reply_to(message, response_text)


# TODO: BUG - sending message exception if it parses markdown with underlines -> _
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
                call_id, "Queue does not exist!🥴🥴🥴 Please contact your chat administrator!")
            return

        if is_queue_entered:
            name, queue = dbhelper.get_queue(chat_id, queue_id)

            edited_text = f"🔴🔴🔴\n" \
                f"\nQueue: {name}" \
                f"\nNumber of members: {len(queue)}" \
                f"\nStatus: ✅\n" \
                f"\nMembers:\n{queue_output(chat_id, queue)}"
            
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
                "Queue does not exist!🥴🥴🥴 Please contact your chat administrator!"
            )
            return

        if is_queue_left:
            name, queue = dbhelper.get_queue(chat_id, queue_id)

            edited_text = f"🔴🔴🔴\n" \
                f"\nQueue: {name}" \
                f"\nNumber of members: {len(queue)}" \
                f"\nStatus: ✅\n" \
                f"\nMembers:\n{queue_output(chat_id, queue)}"

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
    if DEBUG_WITH_POLLING:
        bot.remove_webhook()
        bot.infinity_polling()
    else:
        app = flask.Flask(__name__)

        # Process webhook calls
        @app.route(config.WEBHOOK_URL_PATH, methods=['POST'])
        def webhook():
            # r = flask.request.get(WEBHOOK_URL_PATH)
            # print(r)
            if flask.request.headers.get('content-type') == 'application/json':
                json_string = flask.request.get_data().decode('utf-8')
                update = telebot.types.Update.de_json(json_string)
                bot.process_new_updates([update])
                return ''
            else:
                flask.abort(403)

        bot.remove_webhook()
        # Delay for correct webhook setting
        time.sleep(1)

        r = bot.set_webhook(url=config.WEBHOOK_URL_BASE +
                            config.WEBHOOK_URL_PATH)
        print(r)

        app.run(host=config.WEBHOOK_LISTEN,
                port=config.WEBHOOK_PORT,
                debug=True)

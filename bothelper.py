from re import findall


def extract_user_id(string: str) -> list:
    """
    Finds all telegram user IDs (9 digits) in string and returns them in list.

    :param string: string for searching
    :return: list if user IDs
    """
    return findall(r"\d{9}", string)


def pre_format(string: str) -> str:
    """
    Wraps string in tags <pre>.

    :param string: string to wrap
    :return: wrapped string
    """
    return f"<pre>{string}</pre>"


def is_in_line(text: str, username: str or None) -> bool:
    """
    Checks if a person with the specified username is in the queue. Returns True if it is.

    *This method works with text representation of queue. It takes string value of message text
    and extracts queue from it into the list.*

    :param text: message text as a representation of the queue
    :param username: username of checked user
    :return: True if username contained in the queue
    """
    user_info_list = [string.split(" ", 1) for string in
                      text.split("\n")[2:]]  # List of lists with usernames and numbers of each user
    username_list = [user_info[1].split("@")[-1] for user_info in user_info_list]
    new_username_list = [extract_user_id(us)[0] if any(extract_user_id(us)) else us for us in username_list]

    return str(username) in new_username_list


def is_busy(text: str, number: int) -> bool:
    """
    Checks if the specified number in queue is busy. Returns True if it is.

    *This method works with text representation of queue. It takes string value of message text
    and extracts queue from it into the list.*

    :param text: message text as a representation of the queue
    :param number: number in queue for check
    :return: True if specified number is busy
    """
    user_info_list = [string.split() for string in text.split("\n")[2:]]
    busy_numbers = [int(user_info[0][:-1]) for user_info in user_info_list]

    return number in busy_numbers


def find_free_place(text: str) -> int:
    """
    Finds first free place in queue and return its number. If there are no free places returns -1.

    *This method works with text representation of queue. It takes string value of message text
    and extracts queue from it into the list.*

    :param text: message text as a representation of the queue
    :return: number of free place or -1 if there is no free space in queue
    """
    user_list = [string.split() for string in text.split("\n")[2:]]
    busy_numbers = [int(user_info[0][:-1]) for user_info in user_list]

    for i in range(1, 31):
        if i not in busy_numbers:
            return i

    return -1


def username_format(from_user) -> str:
    """
    Checks username for None (if user has not username). If it has, returns its username
    in telegram format @<username>, else returns html markup with anchor link to specified user.
    In this case, the link to the user profile is generated via his ID.

    :param from_user: json string with information about user
    :return: formatted user link
    """
    if from_user.username is None:
        return f"<a href=\"tg://user?id={from_user.id}\">{from_user.first_name} {from_user.last_name}</a>"
    else:
        return f"@{from_user.username}"

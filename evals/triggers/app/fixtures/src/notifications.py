"""Delivers a message to a user over one channel."""


def send(channel: str, user: dict, text: str) -> str:
    if channel == "email":
        return "email:" + user["email"] + ":" + text
    elif channel == "sms":
        return "sms:" + user["phone"] + ":" + text
    else:
        raise ValueError("unknown channel: " + channel)

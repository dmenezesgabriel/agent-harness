"""Support-ticket response deadline in hours, by ticket priority."""


def response_hours(priority: str) -> int:
    if priority == "low":
        return 72
    elif priority == "normal":
        return 24
    elif priority == "high":
        return 8
    else:
        raise ValueError("unknown priority: " + priority)

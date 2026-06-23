import os
from .shared import clear


def handle_log_mode(key, prev_key):
    print(f"{key=}")

    if key == "CTRL_T" and prev_key == "CTRL_T":
        size = os.get_terminal_size()
        print(f"columns: {size.columns} lines: {size.lines}")

    if key == "CTRL_W":
        clear()

    return False
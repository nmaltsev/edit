import sys

def clear():
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()


def move_cursor(x, y):
    sys.stdout.write(f"\x1b[{y+1};{x+1}H")
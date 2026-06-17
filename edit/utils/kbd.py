import sys
import tty
import termios

# =========================================================
# BASE KEY MAPPINGS
# =========================================================

ANSI_KEYS = {
    "A": "UP",
    "B": "DOWN",
    "C": "RIGHT",
    "D": "LEFT",
    "H": "HOME",
    "F": "END",
}

ANSI_TILDE_KEYS = {
    "1": "HOME",
    "2": "INSERT",
    "3": "DELETE",
    "4": "END",
    "5": "PAGE_UP",
    "6": "PAGE_DOWN",
    "7": "HOME",
    "8": "END",
}

CTRL_KEYS = {
    "\x03": "CTRL_C",
    "\x04": "CTRL_D",
    "\x08": "BACKSPACE",
    "\x7f": "BACKSPACE",
    "\r": "ENTER",
    "\n": "ENTER",
    "\t": "TAB",
    "\x1b": "ESC",
}

# ANSI modifier codes
# 2=Shift, 3=Alt, 5=Ctrl, 6=Ctrl+Shift ...
MODIFIERS = {
    2: "SHIFT",
    3: "ALT",
    4: "ALT+SHIFT",
    5: "CTRL",
    6: "CTRL+SHIFT",
    7: "CTRL+ALT",
    8: "CTRL+ALT+SHIFT",
}

BRACKETED_PASTE_BEGIN = "\x1b[200~"
BRACKETED_PASTE_END = "\x1b[201~"


# =========================================================
# POSIX KEY READER
# =========================================================

def _read_escape_sequence():
    """
    Read full ANSI escape sequence after ESC.
    """
    seq = ""

    while True:
        ch = sys.stdin.read(1)
        seq += ch

        if ch.isalpha() or ch == "~":
            break

    return seq


def _read_bracketed_paste():
    """
    Read terminal bracketed paste payload.
    """
    data = []
    tail = ""

    while True:
        ch = sys.stdin.read(1)

        data.append(ch)
        tail += ch

        if len(tail) > len(BRACKETED_PASTE_END):
            tail = tail[-len(BRACKETED_PASTE_END):]

        if tail.endswith(BRACKETED_PASTE_END):
            data = data[:-len(BRACKETED_PASTE_END)]
            break

    text = "".join(data)

    return (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def _normalize_modifier_key(modifier, key):
    """
    Normalize combinations to match editor expectations.
    """

    if key in ("UP", "DOWN", "LEFT", "RIGHT"):
        if modifier in ("ALT+SHIFT", "CTRL+ALT+SHIFT"):
            return f"SHIFT+{key}"

        if modifier in ("CTRL+SHIFT", "CTRL+ALT"):
            return f"CTRL+{key}"

    if key in ("PAGE_UP", "PAGE_DOWN"):
        if modifier:
            return key

    return f"{modifier}+{key}" if modifier else key


def _decode_escape_sequence(seq):
    """
    Decode ANSI escape sequences.
    """

    if not seq:
        return "ESC"

    if seq == "[200~":
        return "__BRACKETED_PASTE__"

    if not seq.startswith("["):
        if len(seq) == 1:
            ch = seq

            if ch.isalpha():
                return f"ALT+{ch.upper()}"

            if ch.isdigit():
                return f"ALT+{ch}"

        return "ESC"

    body = seq[1:]

    if body in ANSI_KEYS:
        return ANSI_KEYS[body]

    if ";" in body:
        _, rest = body.split(";", 1)

        mod_code = ""
        key_code = ""

        for ch in rest:
            if ch.isdigit():
                mod_code += ch
            else:
                key_code += ch

        modifier = ""

        if mod_code.isdigit():
            modifier = MODIFIERS.get(
                int(mod_code),
                "",
            )

        if key_code.endswith("~"):
            key = ANSI_TILDE_KEYS.get(
                key_code[:-1],
                key_code[:-1],
            )
        else:
            key = ANSI_KEYS.get(
                key_code,
                key_code,
            )

        return _normalize_modifier_key(
            modifier,
            key,
        )

    if body.endswith("~"):
        code = body[:-1]

        return ANSI_TILDE_KEYS.get(
            code,
            code,
        )

    return seq


# =========================================================
# MAIN API
# =========================================================

def get_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)

        ch = sys.stdin.read(1)

        if ch == "\x1b":
            seq = _read_escape_sequence()

            if seq == "[200~":
                return _read_bracketed_paste()

            return _decode_escape_sequence(seq)

        if ch in CTRL_KEYS:
            return CTRL_KEYS[ch]

        code = ord(ch)

        if 1 <= code <= 26:
            return f"CTRL_{chr(code + 64)}"

        return ch

    finally:
        termios.tcsetattr(
            fd,
            termios.TCSADRAIN,
            old,
        )


# ---------- TERMINAL ----------
def clear():
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()


def move_cursor(x, y):
    sys.stdout.write(
        f"\x1b[{y+1};{x+1}H"
    )
import re

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text):
    return ANSI_RE.sub("", text)


def visible_len(text):
    return len(strip_ansi(text))


def fill(text, max_width):
    visible = visible_len(text)

    if visible >= max_width:
        out = []
        count = 0
        i = 0

        while i < len(text) and count < max_width:
            if text[i] == "\033":
                end = text.find("m", i)

                if end == -1:
                    break

                out.append(text[i:end + 1])
                i = end + 1
                continue

            out.append(text[i])
            count += 1
            i += 1

        out.append("\033[0m")

        return "".join(out)

    return text + (" " * (max_width - visible))

def trim_name(name: str, max_len: int) -> str:
  if (len(name) > max_len):
    return name[:(max_len - 3 - 5)] + '...' + name[-5:]
  else:
    return fill(name, max_len)

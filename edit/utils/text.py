def fill(text, max_width):
    if len(text) >= max_width:
        return text[0:max_width]
    else:
        return text + " " * (max_width - len(text))
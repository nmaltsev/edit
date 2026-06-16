from ..editor_helpers import fill

def trim_path(path: str, max_len: int) -> str:
    if (len(path) - 3 > max_len):
        return '...' + path[-(max_len - 3):]
    else:
        return fill(path, max_len)

def trim_name(name: str, max_len: int) -> str:
    if (len(path) > max_len):
        return path[:(max_len - 3 - 5)] + '...' + path[-5:]
    else:
        return fill(name, max_len)
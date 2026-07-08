import os
import shutil

def load_file(path:str):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            return lines or [""]
        except Exception as exc:
            print(f"There is error while processing {path} {exc.__class__}")
            raise exc
    return [""]


def save_file(path:str, doc_lines: list[str]):
    with open(path,"w",encoding="utf-8") as f:
        f.write("\n".join(doc_lines))

def rm_path(path:str):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)

def extend_path(path: str, base_dir: str) -> str:
    """
    Return an absolute path.

    - Relative paths are interpreted relative to base_dir.
    - Absolute paths are returned unchanged.
    - '~' is expanded to the user's home directory.
    - '.', '..' are resolved.
    """
    # Expand ~
    path = os.path.expanduser(path)

    # If already absolute, just normalize it
    if os.path.isabs(path):
        return os.path.normpath(path)

    # Otherwise make it relative to base_dir
    return os.path.normpath(os.path.join(base_dir, path))

def find_files(root_path, pattern):
    results = []

    pattern = pattern.lower()

    for root, dirs, files in os.walk(root_path):
        for filename in files:
            if pattern in filename.lower():
                results.append(os.path.join(root, filename))

    return results
import os
import shutil
import locale

encodings = (
    "utf-8",
    locale.getpreferredencoding(False),
    "utf-8-sig",   # UTF-8 with BOM
    "cp1252",      # Windows Western Europe
    "latin-1",     # Never fails
)

def load_file(path: str):
    """
    Load a text file into a list of lines.

    Tries several common encodings before giving up.
    Returns [""] for missing or empty files.
    """
    if not os.path.exists(path):
        return [""]
  
    last_exc = None

    for encoding in encodings:
        try:
            with open(path, "r", encoding=encoding) as f:
                lines = f.read().splitlines()
            return lines or [""]
        except UnicodeDecodeError as exc:
            last_exc = exc
            continue
        except Exception as exc:
            print(f"There is error while processing {path}: {exc}")
            raise

    # Should never happen because latin-1 can decode any byte sequence,
    # but keep this for completeness.
    raise last_exc

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

# Directories that should never be traversed. 
BLACKLISTED_DIRS = { "__pycache__", "node_modules" }

def find_files(root_path, pattern):
    """
    Search for files whose relative path contains the given pattern.

    Examples:
        "file.py"        -> matches any file.py
        "utils/file.py"  -> matches .../utils/file.py
        "src/utils"      -> matches files under src/utils/

    Hidden directories (starting with ".") are not traversed.
    """
    results = []

    pattern = pattern.strip().lower().replace("\\", "/")

    for root, dirs, files in os.walk(root_path, followlinks=True):
        # Prevent os.walk from descending into hidden directories.
        dirs[:] = [directory for directory in dirs if not directory.startswith(".") and directory not in BLACKLISTED_DIRS]

        for filename in files:
            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, root_path)
            normalized_path = relative_path.replace(os.sep, "/").lower()

            if pattern in normalized_path:
                results.append(full_path)

    return results

def split_path(path: str) -> tuple[str, str]:
    return os.path.split(path)
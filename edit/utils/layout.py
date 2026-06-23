import os
from edit.utils.kbd import get_key, clear
from edit.utils.ui import trim_path, trim_name
from edit.file_helpers import load_file, save_file, rm_path
from edit.editor_helpers import print_status, initial_set
from edit.file_browser_helpers import draw_file_browser, process_file_browser_key

def draw_status_line(state, browser):
    # TODO initialize in a dedicated block
    directory = getattr(browser, "current_path", os.getcwd())
    directory = directory.replace("\\", "/")

    if not directory.endswith("/"):
        directory += "/"

    file_path = state.file_path

    if file_path is not None:
        file_path = state.file_path.replace("\\", "/")
        file_path = trim_path(file_path, 50)

    directory = trim_path(directory, 29)

    status = f"{directory}|{file_path or ''}"

    print("\033[1;2H", end="")
    print("\033[2K", end="")
    print(status, end="")

def redraw_all(state, selectionState, browser):
    draw_status_line(state, browser)
    draw_file_browser(browser)

    if state.file_path:
        initial_set(state, selectionState)

def resize_layout(state, browser):
    size = os.get_terminal_size()

    status_line_width = 1
    browser_width = 30
    editor_width = max(
        1,
        size.columns - browser_width - status_line_width,
    )

    # Reserve one terminal row for the editor status bar.
    editor_height = max(1, size.lines - 2)

    state.view_box = (
        browser_width + status_line_width,
        1,
        editor_width,
        editor_height,
    )

    browser.view_box = (
        0,
        1,
        browser_width,
        editor_height,
    )

    browser.refresh()

def prompt_text(message):
    clear()

    print(message)
    print("> ", end="", flush=True)

    value = ""

    while True:
        key = get_key()

        if key == "ENTER":
            print()
            return value.strip()

        if key == "ESC":
            return None

        if key == "BACKSPACE":
            if value:
                value = value[:-1]
                print("\b \b", end="", flush=True)
            continue

        if len(key) == 1:
            value += key
            print(key, end="", flush=True)

def find_files(root_path, pattern):
    results = []

    pattern = pattern.lower()

    for root, dirs, files in os.walk(root_path):
        for filename in files:
            if pattern in filename.lower():
                results.append(
                    os.path.join(root, filename)
                )

    return results


def show_find_results(results):
    clear()

    if not results:
        print("No matches found.")
        print()
        print("Press any key...")
        get_key()
        return

    for path in results:
        print(os.path.basename(path))
        print(path)
        print()

    print("Press any key...")
    get_key()

def confirm_delete(path):
    answer = prompt_text(f"Delete '{os.path.basename(path)}'? (y/n)")
    return answer and answer.lower() == "y"


def reset_editor(state, selectionState):
    state.doc_lines = [""]
    state.file_path = None
    state.modified = False
    state.view_offset = 0
    state.cursor_offset = [0, 0]

    selectionState.clear_selection()


def open_editor_file(state, selectionState, path):
    state.file_path = path
    state.doc_lines = load_file(path)

    if not state.doc_lines:
        state.doc_lines = [""]

    state.modified = False
    state.view_offset = 0
    state.cursor_offset = [0, 0]

    selectionState.clear_selection()
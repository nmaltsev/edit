import os

from edit import ENABLE_TABS
from edit.utils.kbd import get_key, clear, move_cursor
from edit.utils.ui import trim_path
from edit.file_helpers import load_file
from edit.editor_helpers import print_status, initial_set
from edit.file_browser_helpers import draw_file_browser
from edit.state import DocumentState


def draw_status_line(state, browser):
    directory = getattr(browser, "current_path", os.getcwd()).replace("\\", "/")

    if not directory.endswith("/"):
        directory += "/"

    file_path = state.document.path

    if file_path is not None:
        file_path = trim_path(file_path.replace("\\", "/"), 50)

    directory = trim_path(directory, 29)

    print("\033[1;2H", end="")
    print("\033[2K", end="")
    print(f"{directory}|{file_path or ''}", end="")


def draw_tab_panel(state):
    if not ENABLE_TABS:
        return

    x, y, width, _ = state.tab_box
    move_cursor(x, y)

    parts = []

    for index, document in enumerate(state.open_tabs):
        name = os.path.basename(document.path or "Untitled")
        is_active = index == state.active_tab_index
        is_selected = index == state.tab_selected_index

        if is_active:
            name = f"[{name}]"

        if is_selected:
            name = f"<{name}>"

        parts.append(name)

    text = " ".join(parts)

    print(text[:width].ljust(width), end="")

    move_cursor(x, y + 1)
    print("-" * width, end="")


def redraw_all(state, selectionState, browser):
    draw_status_line(state, browser)
    draw_file_browser(browser)
    draw_tab_panel(state)

    if state.document.path:
        initial_set(state, selectionState)


def resize_layout(state, browser):
    size = os.get_terminal_size()

    browser_width = 30
    status_line_width = 1
    tabs_height = 2 if ENABLE_TABS else 0

    editor_width = max(1, size.columns - browser_width - status_line_width)
    editor_height = max(1, size.lines - 2 - tabs_height)

    state.tab_box = (browser_width + status_line_width, 1, editor_width, tabs_height)
    state.view_box = (browser_width + status_line_width, 1 + tabs_height, editor_width, editor_height)
    browser.view_box = (0, 1, browser_width, size.lines - 1)

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
                results.append(os.path.join(root, filename))

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
    state.document = DocumentState()
    selectionState.clear_selection()


def open_editor_file(state, selectionState, path):
    # TODO use findExistingTabByPath
    existing = state.findExistingTabByPath(path)
    # existing = None

    # for index, document in enumerate(state.open_tabs):
    #     if document.path == path:
    #         existing = index
    #         break

    if existing is None:
        document = DocumentState(
            path=path,
            doc_lines=load_file(path) or [""],
        )

        state.open_tabs.append(document)
        state.active_tab_index = len(state.open_tabs) - 1
    else:
        state.active_tab_index = existing

    state.tab_selected_index = state.active_tab_index
    state.document = state.open_tabs[state.active_tab_index]

    selectionState.clear_selection()

# DEPRECATED
# def save_active_tab_state(state):
#     """
#     No copying is required because EditorState.document references the
#     active DocumentState instance stored in open_tabs.
#     """
#     if state.active_tab_index < 0:
#         return

#     if state.active_tab_index >= len(state.open_tabs):
#         return

#     state.open_tabs[state.active_tab_index] = state.document


def activate_tab(state, selectionState, index):
    if index < 0 or index >= len(state.open_tabs):
        return

    state.save_active_tab_state()
    state.active_tab_index = index
    state.tab_selected_index = index
    state.document = state.open_tabs[index]
    selectionState.clear_selection()
# ./edit/utils/layout.py
import os

from edit import ENABLE_TABS
from edit.utils.kbd import read_sequence
from edit.utils.terminal import clear, move_cursor
from edit.utils.ui import trim_path
from edit.utils.file_helpers import load_file
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
        if document.is_viewer:
            name = f"~{name}"
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
        key = read_sequence()

        if key == "ENTER":
            print()
            return value.strip()

        if key == "CTRL_Q":
            return None

        if key == "BACKSPACE":
            if value:
                value = value[:-1]
                print("\b \b", end="", flush=True)

            continue

        if len(key) == 1:
            value += key
            print(key, end="", flush=True)

def prompt_text2(message, search_cb, render_cb):
    clear()

    print(message)
    print("> ", end="", flush=True)

    value = ""
    line = 0
    offset = 0

    output_height = 10

    # Initial search
    results = search_cb(value)
    result_count = len(results)
    render_cb(results, value, line, offset)

    while True:
        key = read_sequence()

        if key == "ENTER":
            print()

            index = offset + line
            if result_count and index < result_count:
                return results[index]

            return value.strip()

        if key == "DEL":
            return None

        if key == "DOWN" or key == "UP":
            if result_count == 0:
                continue

            if key == "DOWN":
                # Move down one result
                if offset + line < result_count - 1:
                    if line < min(output_height - 1, result_count - offset - 1):
                        line += 1
                    else:
                        offset += 1

            else:  # UP
                # Move up one result
                if offset + line > 0:
                    if line > 0:
                        line -= 1
                    else:
                        offset -= 1

            # Redraw only - do NOT search again
            render_cb(results, value, line, offset)
            continue

        if key == "BACKSPACE":
            if value:
                value = value[:-1]
                print("\b \b", end="", flush=True)

                line = 0
                offset = 0

                # Search again because the pattern changed
                results = search_cb(value)
                result_count = len(results)
                render_cb(results, value, line, offset)
            continue

        if len(key) == 1:
            value += key
            print(key, end="", flush=True)

            line = 0
            offset = 0

            # Search again because the pattern changed
            results = search_cb(value)
            result_count = len(results)
            render_cb(results, value, line, offset)
            
def show_find_results(results):
    # TODO: deprecated
    clear()

    if not results:
        print("No matches found.")
        print()
        print("Press any key...")
        read_sequence()
        return

    for path in results:
        print(os.path.basename(path))
        print(path)
        print()

    print("Press any key...")
    read_sequence()


def confirm_delete(path):
    answer = prompt_text(f"Delete '{os.path.basename(path)}'? (y/n)")
    return answer and answer.lower() == "y"


def reset_editor(state, selectionState):
    state.document = DocumentState()
    selectionState.clear_selection()


def is_markdown_path(path):
    if not path:
        return False
    lower = path.lower()
    return lower.endswith(".md") or lower.endswith(".markdown")


def open_editor_file(state, selectionState, path, is_viewer=None):
    existing = state.findExistingTabByPath(path)

    if is_viewer is None:
        is_viewer = is_markdown_path(path)

    if existing is None:
        document = DocumentState(
            path=path,
            doc_lines=load_file(path) or [""],
            is_viewer=is_viewer,
        )

        state.open_tabs.append(document)
        state.active_tab_index = len(state.open_tabs) - 1
    else:
        state.active_tab_index = existing

    state.tab_selected_index = state.active_tab_index
    state.document = state.open_tabs[state.active_tab_index]

    selectionState.clear_selection()

def activate_tab(state, selectionState, index):
    if index < 0 or index >= len(state.open_tabs):
        return

    state.save_active_tab_state()
    state.active_tab_index = index
    state.tab_selected_index = index
    state.document = state.open_tabs[index]
    selectionState.clear_selection()
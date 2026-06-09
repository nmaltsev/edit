import sys
import os
import shutil
from enum import Enum
from .utils import get_key, clear
from .file_helpers import load_file, save_file
from .state import EditorState, SelectionState, FileBrowserState
from .editor_helpers import print_status, initial_set, fill
from .process_editor_keys import process_editor_keys
from .file_browser_helpers import draw_file_browser, process_file_browser_key

class MODE(Enum):
    EDIT = 0
    LOG = 1
    MODAL = 2
    FILE_BROWSER = 3
    TAB_BROWSER = 4
    TERM = 5


def trim_path(path: str, max_len: int) -> str:
    if (len(path) - 3 > max_len):
        return '...' + path[-(max_len - 3):]
    else:
        return fill(path, max_len)


def draw_status_line(state, browser):
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
        size.columns - browser_width - status_line_width
    )

    state.view_box = (
        browser_width + status_line_width,
        1,
        editor_width,
        size.lines - 1,
    )

    browser.view_box = (
        0,
        1,
        browser_width,
        size.lines - 1,
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

def prompt_new_name(old_name):
    return prompt_text(
        f"Rename '{old_name}'"
    )


def prompt_search_pattern():
    return prompt_text(
        "Enter file name pattern and press enter"
    )


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
    answer = prompt_text(
        f"Delete '{os.path.basename(path)}'? (y/n)"
    )

    return answer and answer.lower() == "y"

def main(use_tab: bool = False, tab_size: int = 2):
    size = os.get_terminal_size()
    status_line_width = 1
    browser_width = 30
    editor_width = max(1, size.columns - browser_width - status_line_width)

    state = EditorState(
        use_tab=use_tab,
        tab_size=tab_size,
        view_box=(
            browser_width + status_line_width,
            1,
            editor_width,
            size.lines - 1,
        ),
    )

    browser = FileBrowserState(
        view_box=(
            0,
            1,
            browser_width,
            size.lines - 1,
        )
    )

    selectionState = SelectionState()
    mode = MODE.FILE_BROWSER

    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.stat(path)[0] & 0x4000:
            pass
        else:
            state.file_path = sys.argv[1]
            state.doc_lines = load_file(state.file_path)
            mode = MODE.EDIT

    prev_key = None
    modal_payload = None

    clear()
    draw_status_line(state, browser)

    if state.file_path:
        initial_set(state, selectionState)

    draw_file_browser(browser)

    print(end='')
    sys.stdout.flush()

    while True:
        key = get_key()

        # -----------------------------------------
        # Refresh / Resize
        # -----------------------------------------

        if key == "CTRL_R":
            resize_layout(state, browser)

            clear()
            redraw_all(
                state,
                selectionState,
                browser,
            )

            sys.stdout.flush()

            prev_key = key
            continue

        # -----------------------------------------
        # Global shortcuts
        # -----------------------------------------

        if key == "CTRL_P" and (mode == MODE.EDIT or mode == MODE.LOG):
            mode = (MODE.EDIT if mode == MODE.LOG else MODE.LOG)
            clear()

            if mode == MODE.EDIT:
                draw_status_line(state, browser)
                initial_set(state, selectionState)
                draw_file_browser(browser)
                print(end='')
                sys.stdout.flush()
            else:
                print('DEBUG MODE')

            prev_key = key
            continue

        if key == 'ALT+RIGHT':
            if mode == MODE.FILE_BROWSER:
                mode = MODE.EDIT
                draw_status_line(state, browser)
                initial_set(state, selectionState)
                draw_file_browser(browser)
                sys.stdout.flush()
                prev_key = key
                continue
            else:
                mode = MODE.FILE_BROWSER
                draw_status_line(state, browser)
                draw_file_browser(browser)
                sys.stdout.flush()
                prev_key = key
                continue

        if key == "CTRL_Z" and prev_key == "CTRL_Z":
            clear()
            break

        # -----------------------------------------
        # LOG MODE
        # -----------------------------------------

        if mode == MODE.LOG:
            print(f"{key=}")

            if key == "CTRL_T" and prev_key == "CTRL_T":
                size = os.get_terminal_size()
                print(f"columns: {size.columns} lines: {size.lines}")

            if key == "CTRL_W":
                clear()

            prev_key = key
            continue

        # -----------------------------------------
        # MODAL MODE
        # -----------------------------------------

        if mode == MODE.MODAL:
            if modal_payload:
                action = modal_payload.get("action")

                if action == "exit":
                    if key == "y":
                        save_file(state.file_path, state.doc_lines)
                        state.modified = False

                    clear()
                    break

                elif action == "delete":
                    if key == "y":
                        path = modal_payload["path"]

                        try:
                            if os.path.isdir(path):
                                shutil.rmtree(path)
                            elif os.path.exists(path):
                                os.remove(path)
                        except Exception as ex:
                            print_status(state, str(ex))

                        browser.refresh()

                    modal_payload = None
                    mode = MODE.FILE_BROWSER
                    clear()

                    redraw_all(state, selectionState, browser)
                    prev_key = key
                    continue

            prev_key = key
            continue

        # -----------------------------------------
        # EDIT MODE
        # -----------------------------------------

        if mode == MODE.EDIT:
            if key == "CTRL_Q" and prev_key == "CTRL_Q":
                if state.modified:
                    mode = MODE.MODAL
                    modal_payload = {
                        "action": "exit"
                    }

                    print_status(state, "Save before exit? y/n")
                    prev_key = key
                    continue

                clear()
                break

            if key == "CTRL_S":
                save_file(state.file_path, state.doc_lines)
                state.modified = False
                redraw_all(state, selectionState, browser)
                prev_key = key
                continue

            draw_status_line(state, browser)
            draw_file_browser(browser)
            process_editor_keys(key, prev_key, state, selectionState)
            prev_key = key
            continue

        # -----------------------------------------
        # FILE BROWSER MODE
        # -----------------------------------------

        if mode == MODE.FILE_BROWSER:
            result = process_file_browser_key(key, browser, state)

            draw_status_line(state, browser)
            draw_file_browser(browser)
            sys.stdout.flush()

            if result:
                action, path = result

                if action == "OPEN_FILE":
                    state.file_path = path
                    state.doc_lines = load_file(path)

                    if not state.doc_lines:
                        state.doc_lines = [""]

                    state.modified = False
                    state.view_offset = 0
                    state.cursor_offset = [0, 0]

                    selectionState.clear_selection()

                    mode = MODE.EDIT

                    draw_status_line(state, browser)
                    initial_set(state, selectionState)
                    draw_file_browser(browser)

                    sys.stdout.flush()
                    prev_key = key
                    continue

                # elif action == "DELETE":
                #     modal_payload = {
                #         "action": "delete",
                #         "path": path,
                #     }

                #     mode = MODE.MODAL

                #     print_status(
                #         state,
                #         f"Delete '{os.path.basename(path)}'? y/n"
                #     )

                #     prev_key = key
                #     continue
                elif action == "DELETE":
                    if confirm_delete(path):
                        try:
                            if os.path.isdir(path):
                                shutil.rmtree(path)
                            elif os.path.exists(path):
                                os.remove(path)

                        except Exception as ex:
                            clear()
                            redraw_all(
                                state,
                                selectionState,
                                browser,
                            )
                            print_status(state, str(ex))
                            prev_key = key
                            continue

                    browser.refresh()

                    clear()
                    redraw_all(state, selectionState, browser)

                    prev_key = key
                    continue

                elif action == "CREATE_DIR":
                    directory_name = prompt_text("Enter the name of the directory and press enter")

                    if directory_name:
                        try:
                            os.mkdir(
                                os.path.join(
                                    path,
                                    directory_name,
                                )
                            )
                        except Exception as ex:
                            clear()
                            redraw_all(
                                state,
                                selectionState,
                                browser,
                            )
                            print_status(state, str(ex))
                            prev_key = key
                            continue

                    browser.refresh()

                    clear()
                    redraw_all(
                        state,
                        selectionState,
                        browser,
                    )

                    sys.stdout.flush()

                    prev_key = key
                    continue

                elif action == "CREATE_FILE":
                    filename = prompt_text("Enter the name of the file and press enter")

                    if filename:
                        try:
                            full_path = os.path.join(path, filename)

                            with open(full_path, "w", encoding="utf-8"):
                                pass

                        except Exception as ex:
                            clear()
                            redraw_all(state, selectionState, browser)
                            print_status(state, str(ex))
                            prev_key = key
                            continue

                    browser.refresh()

                    clear()
                    redraw_all(state, selectionState, browser)
                    prev_key = key
                    continue
                elif action == "RENAME":
                    new_name = prompt_new_name(os.path.basename(path))

                    if new_name:
                        try:
                            target = os.path.join(os.path.dirname(path), new_name,)
                            os.rename(path, target)
                        except Exception as ex:
                            clear()
                            redraw_all(state, selectionState, browser)
                            print_status(state, str(ex))
                            prev_key = key
                            continue

                    browser.refresh()

                    clear()
                    redraw_all(
                        state,
                        selectionState,
                        browser,
                    )

                    prev_key = key
                    continue

                elif action == "FIND_BY_FNAME":
                    pattern = prompt_search_pattern()

                    if pattern:
                        results = find_files(
                            path,
                            pattern,
                        )

                        show_find_results(results)

                    clear()
                    redraw_all(
                        state,
                        selectionState,
                        browser,
                    )

                    prev_key = key
                    continue

            draw_status_line(state, browser)
            draw_file_browser(browser)

            prev_key = key
            continue

        prev_key = key


if __name__ == "__main__":
    main()
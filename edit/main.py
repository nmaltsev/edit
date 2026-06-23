import sys
import os
from enum import Enum
from .utils.kbd import get_key, clear
from .utils.layout import draw_status_line, redraw_all, resize_layout, prompt_text, find_files, show_find_results, confirm_delete, reset_editor, open_editor_file
from .file_helpers import load_file, save_file, rm_path
from .state import EditorState, SelectionState, FileBrowserState
from .editor_helpers import print_status, initial_set
from .process_editor_keys import process_editor_keys
from .file_browser_helpers import draw_file_browser, process_file_browser_key
from .utils.ui import trim_path, trim_name

class MODE(Enum):
    EDIT = 0
    LOG = 1
    MODAL = 2
    FILE_BROWSER = 3
    TAB_BROWSER = 4
    TERM = 5

def main(use_tab: bool = False, tab_size: int = 2):
    size = os.get_terminal_size()
    status_line_width = 1
    browser_width = 30
    editor_width = max(1, size.columns - browser_width - status_line_width)
    # Reserve one terminal row for the editor status bar.
    editor_height = max(1, size.lines - 2)

    state = EditorState(
        use_tab=use_tab,
        tab_size=tab_size,
        view_box=(
            browser_width + status_line_width,
            1,
            editor_width,
            editor_height,
        ),
    )

    browser = FileBrowserState(
        view_box=(
            0,
            1,
            browser_width,
            editor_height,
        )
    )

    selectionState = SelectionState()
    mode = MODE.FILE_BROWSER

    if len(sys.argv) > 1:
        path = sys.argv[1]
        try:
            if os.stat(path)[0] & 0x4000:
                # If the path is a directory
                browser.current_path = path
                browser.refresh()
            else:
                open_editor_file(
                    state,
                    selectionState,
                    path,
                )
                mode = MODE.EDIT

        except FileNotFoundError:
            browser.current_path = os.getcwd()

    prev_key = None
    modal_payload = None

    clear()
    draw_status_line(state, browser)

    if state.file_path:
        initial_set(state, selectionState)

    draw_file_browser(browser)
    print(end="")
    sys.stdout.flush()

    while True:
        key = get_key()

        # -----------------------------------------
        # Refresh / Resize
        # -----------------------------------------
        if key == "CTRL_R":
            # TODO process_redraw()
            resize_layout(state, browser)
            clear()
            redraw_all(state, selectionState, browser)
            sys.stdout.flush()
            prev_key = key
            continue

        # -----------------------------------------
        # Global shortcuts
        # -----------------------------------------
        if key == "CTRL_P" and (mode == MODE.EDIT or mode == MODE.LOG):
            mode = (MODE.EDIT if mode == MODE.LOG else MODE.LOG)
            #  TODO process_
            clear()

            if mode == MODE.EDIT:
                draw_status_line(state, browser)
                initial_set(state, selectionState)
                draw_file_browser(browser)
                print(end="")
                sys.stdout.flush()
            else:
                print("DEBUG MODE")

            prev_key = key
            continue

        if key == "ALT+RIGHT":
            if mode == MODE.FILE_BROWSER:
                mode = MODE.EDIT

                draw_status_line(state, browser)

                if state.file_path:
                    initial_set(state, selectionState)

                draw_file_browser(browser)

                sys.stdout.flush()
                prev_key = key
                continue

            mode = MODE.FILE_BROWSER
            draw_status_line(state, browser)
            draw_file_browser(browser)
            sys.stdout.flush()
            prev_key = key
            continue

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

                if action == "CLOSE_EDITOR":
                    if key == "y":
                        if state.file_path and state.file_path != "Untitled":
                            save_file(
                                state.file_path,
                                state.doc_lines,
                            )

                    reset_editor(
                        state,
                        selectionState,
                    )

                    mode = MODE.FILE_BROWSER

                    clear()
                    redraw_all(
                        state,
                        selectionState,
                        browser,
                    )

                    prev_key = key
                    continue

                if action == "EXIT_APP":
                    if key == "y":
                        clear()
                        break

                    mode = MODE.FILE_BROWSER
                    modal_payload = None

                    clear()
                    redraw_all(
                        state,
                        selectionState,
                        browser,
                    )

                    prev_key = key
                    continue

            prev_key = key
            continue

        # -----------------------------------------
        # EDIT MODE
        # -----------------------------------------
        if mode == MODE.EDIT:

            if key == "CTRL_Q":
                if state.modified:
                    mode = MODE.MODAL
                    modal_payload = {
                        "action": "CLOSE_EDITOR",
                    }

                    print_status(
                        state,
                        "Save before close? y/n",
                    )

                    prev_key = key
                    continue

                reset_editor(
                    state,
                    selectionState,
                )

                mode = MODE.FILE_BROWSER

                clear()
                redraw_all(
                    state,
                    selectionState,
                    browser,
                )

                prev_key = key
                continue

            if key == "ALT+S":
                target = prompt_text(
                    "Save as file name"
                )

                if target:
                    try:
                        save_file(
                            target,
                            state.doc_lines,
                        )

                        state.file_path = target
                        state.modified = False

                    except Exception as ex:
                        clear()
                        redraw_all(
                            state,
                            selectionState,
                            browser,
                        )
                        print_status(
                            state,
                            str(ex),
                        )

                        prev_key = key
                        continue

                clear()
                redraw_all(
                    state,
                    selectionState,
                    browser,
                )

                prev_key = key
                continue

            if key == "CTRL_S":
                if (
                    not state.file_path
                    or state.file_path == "Untitled"
                ):
                    target = prompt_text(
                        "Save as file name"
                    )

                    if not target:
                        clear()
                        redraw_all(
                            state,
                            selectionState,
                            browser,
                        )

                        prev_key = key
                        continue

                    state.file_path = target

                save_file(
                    state.file_path,
                    state.doc_lines,
                )

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

            if key == "CTRL_Q":
                if prev_key == "CTRL_Q":
                    clear()
                    break

                print_status(
                    state,
                    "Press CTRL_Q again to exit",
                )

                prev_key = key
                continue

            if key == "ALT+N":
                reset_editor(
                    state,
                    selectionState,
                )

                state.file_path = "Untitled"

                mode = MODE.EDIT

                clear()

                draw_status_line(
                    state,
                    browser,
                )

                initial_set(
                    state,
                    selectionState,
                )

                draw_file_browser(
                    browser,
                )

                sys.stdout.flush()

                prev_key = key
                continue

            result = process_file_browser_key(
                key,
                browser,
                state,
            )

            draw_status_line(state, browser)
            draw_file_browser(browser)
            sys.stdout.flush()

            if result:
                action, path = result

                if action == "OPEN_FILE":
                    open_editor_file(
                        state,
                        selectionState,
                        path,
                    )

                    mode = MODE.EDIT

                    draw_status_line(
                        state,
                        browser,
                    )

                    initial_set(
                        state,
                        selectionState,
                    )

                    draw_file_browser(
                        browser,
                    )

                    sys.stdout.flush()

                    prev_key = key
                    continue

                elif action == "DELETE":
                    if confirm_delete(path):
                        try:
                            rm_path(path)
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
                            os.mkdir(os.path.join(path, directory_name))
                        except Exception as ex:
                            clear()
                            redraw_all(state, selectionState, browser)
                            print_status(state, str(ex))
                            prev_key = key
                            continue

                    browser.refresh()

                    clear()
                    redraw_all(state, selectionState, browser)
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
                    new_name = prompt_text(f"Rename '{os.path.basename(path)}'")

                    if new_name:
                        try:
                            target = os.path.join(os.path.dirname(path), new_name)
                            os.rename(path, target)
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

                elif action == "FIND_BY_FNAME":
                    pattern = prompt_text("Enter file name pattern and press enter")

                    if pattern:
                        results = find_files(path, pattern)
                        show_find_results(results)

                    clear()
                    redraw_all(state, selectionState,browser, )
                    prev_key = key
                    continue

            draw_status_line(state, browser)
            draw_file_browser(browser)

            prev_key = key
            continue

        prev_key = key


if __name__ == "__main__":
    main()
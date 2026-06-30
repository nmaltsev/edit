import os
import sys

from ..utils.kbd import clear
from ..utils.layout import (
    redraw_all,
    draw_status_line,
    prompt_text,
    find_files,
    show_find_results,
    confirm_delete,
    reset_editor,
    open_editor_file,
)
from ..editor_helpers import print_status, initial_set
from ..file_browser_helpers import draw_file_browser, process_file_browser_key
from ..file_helpers import rm_path


def handle_file_browser_mode(key, prev_key, mode, state, selectionState, browser):
    if key == "CTRL_Q":
        if prev_key == "CTRL_Q":
            clear()
            return True, mode

        print_status(
            state,
            "Press CTRL_Q again to exit",
        )

        return False, mode

    if key == "ALT+N":
        from ..state import DocumentState

        document = DocumentState(path="Untitled")
        state.open_tabs.append(document)
        state.active_tab_index = len(state.open_tabs) - 1
        state.tab_selected_index = state.active_tab_index
        state.document = document

        selectionState.clear_selection()
        mode = type(mode).EDIT
        clear()

        draw_status_line(state, browser)
        initial_set(state, selectionState)
        draw_file_browser(browser)
        sys.stdout.flush()

        return False, mode

    result = process_file_browser_key(key, browser, state)
    draw_status_line(state, browser)
    draw_file_browser(browser)
    sys.stdout.flush()

    if result:
        action, path = result

        if action == "OPEN_FILE":
            open_editor_file(state, selectionState, path)

            mode = type(mode).EDIT
            redraw_all(state, selectionState, browser)
            sys.stdout.flush()
            print(end='')

            return False, mode

        elif action == "DELETE":
            if confirm_delete(path):
                try:
                    rm_path(path)

                except Exception as ex:
                    clear()

                    redraw_all(state, selectionState, browser)

                    print_status(
                        state,
                        str(ex),
                    )

                    return False, mode

            browser.refresh()
            clear()
            redraw_all(state, selectionState, browser)

            return False, mode

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

                    print_status(
                        state,
                        str(ex),
                    )

                    return False, mode

            browser.refresh()

            clear()

            redraw_all(
                state,
                selectionState,
                browser,
            )

            sys.stdout.flush()

            return False, mode

        elif action == "CREATE_FILE":
            filename = prompt_text("Enter the name of the file and press enter")

            if filename:
                try:
                    full_path = os.path.join(
                        path,
                        filename,
                    )

                    with open(full_path, "w", encoding="utf-8"):
                        pass
                except Exception as ex:
                    clear()
                    redraw_all(state, selectionState, browser)
                    print_status(state, str(ex))
                    sys.stdout.flush()

                    return False, mode

            browser.refresh()
            clear()
            redraw_all(state, selectionState, browser)
            sys.stdout.flush()
            return False, mode

        elif action == "RENAME":
            new_name = prompt_text(
                f"Rename '{os.path.basename(path)}'"
            )

            if new_name:
                try:
                    target = os.path.join(
                        os.path.dirname(path),
                        new_name,
                    )

                    os.rename(
                        path,
                        target,
                    )

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

                    return False, mode

            browser.refresh()

            clear()

            redraw_all(
                state,
                selectionState,
                browser,
            )

            return False, mode

        elif action == "FIND_BY_FNAME":
            pattern = prompt_text(
                "Enter file name pattern and press enter"
            )

            if pattern:
                results = find_files(
                    path,
                    pattern,
                )

                show_find_results(
                    results,
                )

            clear()

            redraw_all(
                state,
                selectionState,
                browser,
            )

            return False, mode

    draw_status_line(
        state,
        browser,
    )

    draw_file_browser(
        browser,
    )

    return False, mode
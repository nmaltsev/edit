import sys, os

from ..utils.kbd import clear
from ..utils.layout import (
    draw_status_line,
    redraw_all,
    prompt_text,
    reset_editor,
    save_active_tab_state,
    draw_tab_panel,
)
from ..file_browser_helpers import draw_file_browser
from ..editor_helpers import print_status
from ..process_editor_keys import process_editor_keys
from ..file_helpers import save_file


def handle_edit_mode(key, mode, modal_payload, state, selectionState, browser):
    document = state.document

    if key == "CTRL_Q":
        save_active_tab_state(state)

        if state.active_tab_index >= 0:
            state.open_tabs.pop(state.active_tab_index)

            if state.open_tabs:
                state.active_tab_index = min(
                    state.active_tab_index,
                    len(state.open_tabs) - 1,
                )

                state.document = state.open_tabs[state.active_tab_index]

                redraw_all(
                    state,
                    selectionState,
                    browser,
                )

                sys.stdout.flush()

                return mode, modal_payload

        reset_editor(
            state,
            selectionState,
        )

        mode = type(mode).FILE_BROWSER

        clear()

        redraw_all(
            state,
            selectionState,
            browser,
        )

        sys.stdout.flush()

        return mode, modal_payload

    if key == "ALT+S":
        target = prompt_text(
            "Save as file name"
        )

        if target:
            try:
                save_file(
                    target,
                    document.doc_lines,
                )

                document.path = target
                document.modified = False

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

                return mode, modal_payload

        clear()

        redraw_all(
            state,
            selectionState,
            browser,
        )

        return mode, modal_payload

    if key == "CTRL_S":
        if (not document.path or document.path == "Untitled"):
            target = prompt_text("Save as file name")

            if not target:
                clear()
                redraw_all(state, selectionState, browser)

                return mode, modal_payload

            target = os.path.expanduser(target)

            if not os.path.isabs(target):
                target = os.path.join(browser.current_path, target)
            document.path = os.path.abspath(target)

        save_file(document.path, document.doc_lines)
        document.modified = False
        redraw_all(state, selectionState, browser)

        return mode, modal_payload

    draw_status_line(state, browser)
    draw_file_browser(browser)
    draw_tab_panel(state)
    process_editor_keys(key, None, state, selectionState)

    save_active_tab_state(state)
    
    return mode, modal_payload
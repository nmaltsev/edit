import sys
from ..utils.kbd import clear
from ..utils.layout import (
    draw_status_line,
    redraw_all,
    prompt_text,
    reset_editor,
    save_active_tab_state, draw_tab_panel
)
from ..file_browser_helpers import draw_file_browser
from ..editor_helpers import print_status
from ..process_editor_keys import process_editor_keys
from ..file_helpers import save_file


def handle_edit_mode(key, mode, modal_payload, state, selectionState, browser):
    if key == "CTRL_Q":
        save_active_tab_state(state)

        if state.active_tab_index >= 0:
            state.open_tabs.pop(state.active_tab_index)

            if state.open_tabs:
                state.active_tab_index = min(
                    state.active_tab_index,
                    len(state.open_tabs) - 1,
                )

                tab = state.open_tabs[state.active_tab_index]

                state.file_path = tab["path"]
                state.doc_lines = tab["doc_lines"]
                state.cursor_offset = tab["cursor_offset"]
                state.view_offset = tab["view_offset"]
                state.modified = tab["modified"]

                redraw_all(state, selectionState, browser)
                # print(end='')
                sys.stdout.flush()

                return mode, modal_payload

        reset_editor(
            state,
            selectionState,
        )

        mode = type(mode).FILE_BROWSER
        clear()
        redraw_all(state,selectionState,browser)
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

                return mode, modal_payload

        clear()

        redraw_all(
            state,
            selectionState,
            browser,
        )

        return mode, modal_payload

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

                return mode, modal_payload

            state.file_path = target

        save_file(
            state.file_path,
            state.doc_lines,
        )

        state.modified = False

        redraw_all(
            state,
            selectionState,
            browser,
        )

        return mode, modal_payload

    draw_status_line(state, browser)
    draw_file_browser(browser)
    draw_tab_panel(state)
    process_editor_keys(key, None, state, selectionState)
    save_active_tab_state(state)
    # TODO update the tab panel

    return mode, modal_payload
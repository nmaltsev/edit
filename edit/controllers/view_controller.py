# ./edit/controllers/view_controller.py
import sys
from ..utils.terminal import clear
from ..utils.layout import draw_status_line, redraw_all, reset_editor, draw_tab_panel
from ..file_browser_helpers import draw_file_browser
from ..process_view_keys import process_view_keys


def handle_view_mode(key, mode, modal_payload, state, selectionState, browser):
    document = state.document

    if key == "CTRL_Q":
        state.save_active_tab_state()

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

                if state.document.is_viewer:
                    return type(mode).VIEW, modal_payload
                return type(mode).EDIT, modal_payload

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

    draw_status_line(state, browser)
    draw_file_browser(browser)
    draw_tab_panel(state)
    process_view_keys(key, None, state, selectionState)
    state.save_active_tab_state()

    return mode, modal_payload
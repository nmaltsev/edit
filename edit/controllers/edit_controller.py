from ..utils.kbd import clear
from ..utils.layout import draw_status_line, redraw_all, prompt_text, reset_editor
from ..file_browser_helpers import draw_file_browser
from ..editor_helpers import print_status
from ..process_editor_keys import process_editor_keys
from ..file_helpers import save_file


def handle_edit_mode(key, mode, modal_payload, state, selectionState, browser):
    if key == "CTRL_Q":
        if state.modified:
            mode = type(mode).MODAL

            modal_payload = {
                "action": "CLOSE_EDITOR",
            }

            print_status(
                state,
                "Save before close? y/n",
            )

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

    draw_status_line(
        state,
        browser,
    )

    draw_file_browser(
        browser,
    )

    process_editor_keys(
        key,
        None,
        state,
        selectionState,
    )

    return mode, modal_payload
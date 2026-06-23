from ..utils.kbd import clear
from ..utils.layout import redraw_all, reset_editor
from ..editor_helpers import print_status


def handle_modal_mode(key, mode, modal_payload, state, selectionState, browser):
    if modal_payload:
        action = modal_payload.get("action")

        if action == "CLOSE_EDITOR":
            if key == "y":
                if state.file_path and state.file_path != "Untitled":
                    from ..file_helpers import save_file

                    save_file(
                        state.file_path,
                        state.doc_lines,
                    )

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

            return False, mode, modal_payload

        if action == "EXIT_APP":
            if key == "y":
                clear()
                return True, mode, modal_payload

            mode = type(mode).FILE_BROWSER
            modal_payload = None

            clear()

            redraw_all(
                state,
                selectionState,
                browser,
            )

            return False, mode, modal_payload

    return False, mode, modal_payload
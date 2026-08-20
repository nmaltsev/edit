import sys
from ..utils.terminal import clear
from ..utils.layout import redraw_all, reset_editor
from ..editor_helpers import print_status
from ..utils.file_helpers import save_file


def handle_modal_mode(key, mode, modal_payload, state, selectionState, browser):
    if modal_payload:
        action = modal_payload.get("action")

        if action == "CLOSE_EDITOR":
            if key == "y":
                if state.document.path:
                    if state.document.path != "Untitled":
                        save_file(state.document.path, state.document.doc_lines)
                    else:
                        # TODO prompt a file name from a layout
                        # TODO save in the browser path
                        # TODO check if the file with such name already exists
                        pass
            
            
            reset_editor(state, selectionState)
            mode = type(mode).FILE_BROWSER
            clear()
            # TODO close the tab and update the
            redraw_all(state, selectionState, browser)
            sys.stdout.flush()

            return False, mode, modal_payload

        # DEPRECATED 
        # if action == "EXIT_APP":
        #     if key == "y":
        #         clear()
        #         return True, mode, modal_payload

        #     mode = type(mode).FILE_BROWSER
        #     modal_payload = None

        #     clear()

        #     redraw_all(
        #         state,
        #         selectionState,
        #         browser,
        #     )

        #     return False, mode, modal_payload

    return False, mode, modal_payload
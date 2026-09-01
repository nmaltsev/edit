import sys, os
from ..utils.terminal import clear
from ..utils.layout import draw_status_line, redraw_all, prompt_text, reset_editor, draw_tab_panel, draw_file_browser
from ..file_browser_helpers import draw_file_browser
from ..editor_helpers import print_status, initial_set
from ..process_editor_keys import process_editor_keys
from ..utils.file_helpers import save_file, extend_path
from ..utils.kbd import read_sequence
# import time
# time.sleep(5)

def handle_edit_mode(key, mode, modal_payload, state, selectionState, browser):
    document = state.document

    if key == "CTRL_Q":
        if state.document.modified:
            print_status(state, "Save before close? y/n")
            key = read_sequence()
            file_list_changed = False
            if key == 'y':
                if (not document.path or document.path == "Untitled"):
                    inputed_path = prompt_text("Save as file name")

                    if not inputed_path:
                        clear()
                        redraw_all(state, selectionState, browser)
                        # initial_set(state, selectionState)
                        return mode, modal_payload

                    document.path = extend_path(inputed_path, browser.current_path)
                    file_list_changed = True
                save_file(document.path, document.doc_lines)
                if file_list_changed:
                    browser.refresh()
                    clear()
                    redraw_all(state, selectionState, browser)
                    # sys.stdout.flush()
                document.modified = False
                return mode, modal_payload        
            elif key != 'n':
                # Press any other key - do nothing
                initial_set(state, selectionState)
                return mode, modal_payload

        state.save_active_tab_state()

        if state.active_tab_index >= 0:
            state.open_tabs.pop(state.active_tab_index)

            if state.open_tabs:
                state.active_tab_index = min(state.active_tab_index, len(state.open_tabs) - 1)
                state.document = state.open_tabs[state.active_tab_index]
                redraw_all(state, selectionState, browser)
                sys.stdout.flush()

                if state.document.is_viewer:
                    # return type(mode).VIEW, modal_payload
                    return type(mode).EDIT, modal_payload
                return mode, modal_payload

        reset_editor(state, selectionState)
        mode = type(mode).FILE_BROWSER
        clear()
        redraw_all(state, selectionState, browser)
        sys.stdout.flush()

        return mode, modal_payload

    if key == "ALT+CTRL_S":
        target = extend_path(prompt_text("Save as file name"), browser.current_path)

        if target:
            try:
                save_file(target, document.doc_lines)
                document.path = target
                document.modified = False
            except Exception as ex:
                clear()
                redraw_all(state, selectionState, browser)
                print_status(state, str(ex))
                return mode, modal_payload
        browser.refresh()
        clear()
        redraw_all(state, selectionState, browser)
        return mode, modal_payload

    if key == "CTRL_S":
        file_list_changed = False
        if (not document.path or document.path == "Untitled"):
            target = prompt_text("Save as file name")

            if not target:
                clear()
                redraw_all(state, selectionState, browser)

                return mode, modal_payload

            document.path = extend_path(target, browser.current_path)
            file_list_changed = True

        save_file(document.path, document.doc_lines)
        document.modified = False
        if file_list_changed:
            browser.refresh()
            # Clear and redraw UI to hide the prompt artefacts 
            clear()
            redraw_all(state, selectionState, browser)
        else:
            # Just update ui
            initial_set(state, selectionState)

        return mode, modal_payload

    draw_status_line(state, browser)
    draw_file_browser(browser)
    draw_tab_panel(state)
    process_editor_keys(key, None, state, selectionState)
    state.save_active_tab_state()
    
    return mode, modal_payload
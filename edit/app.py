# ./edit/app.py
import os
import sys
from enum import Enum

from .utils.kbd import read_sequence
from .utils.terminal import clear
from .utils.layout import draw_status_line, redraw_all, resize_layout, prompt_text2
from .state import EditorState, SelectionState, FileBrowserState, DocumentState
from .editor_helpers import initial_set, print_status
from .utils.layout import reset_editor
from .utils.file_helpers import load_file, extend_path, find_files
from .file_browser_helpers import draw_file_browser
from .process_editor_keys import process_editor_keys
from .controllers.edit_controller import handle_edit_mode
from .controllers.file_browser_controller import handle_file_browser_mode
from .controllers.log_controller import handle_log_mode
from .controllers.view_controller import handle_view_mode
from .utils.layout import open_editor_file, is_markdown_path, open_editor_file
from .utils.file_search_helpers import get_result_render
from edit.states.view_box import ViewBox


class MODE(Enum):
    EDIT = 0
    LOG = 1
    # MODAL = 2
    FILE_BROWSER = 3
    TAB_BROWSER = 4
    TERM = 5
    VIEW = 6


class EditorApplication:

    def __init__(self, use_tab: bool = False, tab_size: int = 2):
        status_line_width = 1
        browser_width = 30
        tabs_height = 2

        editor_view_box = ViewBox(browser_width + status_line_width, 1 + tabs_height, None, None)
        browser_view_box = ViewBox(0, 2, browser_width, None)
        tabs_view_box = ViewBox(browser_width + status_line_width, 1, None, tabs_height)

        self.state = EditorState(
            use_tab=use_tab,
            tab_size=tab_size,
            view_box=editor_view_box
        )

        self.browser = FileBrowserState(view_box=browser_view_box)
        self.selectionState = SelectionState()
        self.mode = MODE.FILE_BROWSER
        self.prev_key = None
        self.modal_payload = None
        self.state.tab_box = tabs_view_box
        self.state.tab_selected_index = 0


    def initialize(self):
        if len(sys.argv) > 1:
            path = os.path.expanduser(sys.argv[1])

            if os.path.isdir(path):
                # Open directory in the file browser.
                self.browser.current_path = path
                self.browser.refresh()

            elif os.path.exists(path):
                # Existing file.
                open_editor_file(self.state, self.selectionState, path, is_markdown_path(path))
                # self.mode = MODE.VIEW if is_markdown_path(path) else MODE.EDIT
                self.mode = MODE.EDIT
            else:
                # New file:
                if not os.path.isabs(path):
                    path = os.path.abspath(path)

                document = DocumentState(path=path)
                self.state.open_tabs.append(document)
                self.state.active_tab_index = len(self.state.open_tabs) - 1
                self.state.tab_selected_index = self.state.active_tab_index
                self.state.document = document

                self.selectionState.clear_selection()
                self.mode = MODE.EDIT

        clear()
        redraw_all(self.state, self.selectionState, self.browser)
        sys.stdout.flush()


    def handle_global_shortcuts(self, key):
        if key == "CTRL_R":
            tab = self.state.get_active_document()
            if tab is not None:
                tab.doc_lines = load_file(tab.path) or [""]
                self.state.document = tab

            resize_layout(self.state, self.browser)
            clear()
            redraw_all(self.state, self.selectionState, self.browser)
            sys.stdout.flush()
            return True

        if key == "CTRL_P":
            promted_path = prompt_text2(
                "Enter file name pattern and press enter",
                (None,None,self.state.view_box[2],None),
                lambda value: find_files(self.browser.current_path, value.strip()),
                get_result_render(self.browser.current_path),
            )
            if promted_path:
                promted_path = extend_path(promted_path, self.browser.current_path)
                if os.path.isdir(promted_path):
                    self.browser.navigate(promted_path)
                    self.mode = type(self.mode).FILE_BROWSER
                elif os.path.exists(promted_path):
                    read_only = False # is_markdown_path(promted_path)
                    open_editor_file(self.state, self.selectionState, promted_path, read_only)
                    # TODO decide when to open in RO mode or not
                    # self.mode = type(self.mode).VIEW if is_markdown_path(promted_path) else type(self.mode).EDIT
                    self.mode = type(self.mode).EDIT

            clear()
            redraw_all(self.state, self.selectionState, self.browser)
            return True
            
        # Temporary disabled
        # if key == "CTRL_P" and (self.mode == MODE.EDIT or self.mode == MODE.VIEW or self.mode == MODE.LOG):
        #     if self.mode == MODE.LOG:
        #         doc = self.state.get_active_document()
        #         self.mode = MODE.VIEW if doc and doc.is_viewer else MODE.EDIT
        #     else:
        #         self.mode = MODE.LOG
        #     clear()

        #     if self.mode in (MODE.EDIT, MODE.VIEW):
        #         draw_status_line(self.state, self.browser)
        #         initial_set(self.state, self.selectionState)
        #         draw_file_browser(self.browser)
        #         print(end="")
        #         sys.stdout.flush()
        #     else:
        #         print("DEBUG MODE")

        #     return True
        if key == "CTRL_F":
            # TODO
            pass

        if key in ("CTRL_J", "CTRL_K", "ALT+RIGHT", "CTRL_L"):
            if key == "ALT+RIGHT":
                if self.mode == MODE.FILE_BROWSER:
                    self.mode = MODE.TAB_BROWSER
                elif self.mode == MODE.TAB_BROWSER:
                    doc = self.state.get_active_document()
                    # self.mode = MODE.VIEW if doc and doc.is_viewer else MODE.EDIT
                    self.mode = MODE.EDIT
                else:
                    self.mode = MODE.FILE_BROWSER
            elif key == "CTRL_J":
                self.mode = MODE.TAB_BROWSER
            elif key == "CTRL_K":
                doc = self.state.get_active_document()
                # self.mode = MODE.VIEW if doc and doc.is_viewer else MODE.EDIT
                self.mode = MODE.EDIT
            elif key == "CTRL_L":
                self.mode = MODE.FILE_BROWSER

            clear()
            redraw_all(self.state, self.selectionState, self.browser)
            return True

        return False

    def run(self):
        self.initialize()

        while True:
            key = read_sequence()

            if self.handle_global_shortcuts(key):
                self.prev_key = key
                continue

            if self.mode == MODE.LOG:
                if handle_log_mode(key, self.prev_key):
                    break

                self.prev_key = key
                continue

            if self.mode == MODE.TAB_BROWSER:
                from .utils.layout import activate_tab, draw_tab_panel

                if key == "LEFT" and self.state.open_tabs:
                    self.state.tab_selected_index = (
                        self.state.tab_selected_index - 1
                    ) % len(self.state.open_tabs)

                elif key == "RIGHT" and self.state.open_tabs:
                    self.state.tab_selected_index = (
                        self.state.tab_selected_index + 1
                    ) % len(self.state.open_tabs)

                elif key == "CTRL_O":
                    # to change the current directory
                    if self.state.tab_selected_index < len(self.state.open_tabs):
                        tab = self.state.open_tabs[self.state.tab_selected_index]

                        if tab is not None:
                            next_path = os.path.dirname(tab.path)
                            self.mode = MODE.FILE_BROWSER
                            self.browser.current_path = next_path
                            self.browser.refresh()
                            draw_file_browser(self.browser)

                elif key == "ENTER":
                    activate_tab(
                        self.state,
                        self.selectionState,
                        self.state.tab_selected_index,
                    )
                    initial_set(self.state, self.selectionState)
                    doc = self.state.get_active_document()
                    # self.mode = MODE.VIEW if doc and doc.is_viewer else MODE.EDIT
                    self.mode = MODE.EDIT

                draw_tab_panel(self.state)
                sys.stdout.flush()
                print(end="")
                self.prev_key = key
                continue

            if self.mode == MODE.EDIT:
                handler = handle_view_mode if self.state.document.is_viewer else handle_edit_mode
                self.mode, self.modal_payload = handler(
                    key,
                    self.mode,
                    self.modal_payload,
                    self.state,
                    self.selectionState,
                    self.browser,
                )

                self.prev_key = key
                continue

            if self.mode == MODE.FILE_BROWSER:
                should_break, self.mode = handle_file_browser_mode(
                    key,
                    self.prev_key,
                    self.mode,
                    self.state,
                    self.selectionState,
                    self.browser,
                )

                if should_break:
                    break

                self.prev_key = key
                continue

            self.prev_key = key
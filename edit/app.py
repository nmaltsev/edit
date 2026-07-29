import os
import sys
from enum import Enum

from .utils.kbd import read_sequence
from .utils.terminal import clear
from .utils.layout import draw_status_line, redraw_all, resize_layout
from .state import EditorState, SelectionState, FileBrowserState, DocumentState
from .editor_helpers import initial_set, print_status
from .utils.layout import reset_editor
from .utils.file_helpers import load_file
from .file_browser_helpers import draw_file_browser
from .process_editor_keys import process_editor_keys
from .controllers.edit_controller import handle_edit_mode
from .controllers.file_browser_controller import handle_file_browser_mode
from .controllers.modal_controller import handle_modal_mode
from .controllers.log_controller import handle_log_mode
from .utils.layout import open_editor_file


class MODE(Enum):
    EDIT = 0
    LOG = 1
    MODAL = 2
    FILE_BROWSER = 3
    TAB_BROWSER = 4
    TERM = 5


class EditorApplication:

    def __init__(self, use_tab: bool = False, tab_size: int = 2):
        size = os.get_terminal_size()
        status_line_width = 1
        browser_width = 30
        editor_width = max(1, size.columns - browser_width - status_line_width)

        # Reserve one terminal row for the editor status bar.
        editor_height = max(1, size.lines - 2)

        self.state = EditorState(
            use_tab=use_tab,
            tab_size=tab_size,
            view_box=(
                browser_width + status_line_width,
                1,
                editor_width,
                editor_height,
            ),
        )

        self.browser = FileBrowserState(
            view_box=(
                0,
                1,
                browser_width,
                editor_height,
            )
        )

        self.selectionState = SelectionState()
        self.mode = MODE.FILE_BROWSER
        self.prev_key = None
        self.modal_payload = None

        tabs_height = 2
        self.state.tab_box = (
            browser_width + status_line_width,
            1,
            editor_width,
            tabs_height,
        )
        self.state.tab_selected_index = 0
        self.state.view_box = (
            browser_width + status_line_width,
            1 + tabs_height,
            editor_width,
            max(1, size.lines - 2 - tabs_height),
        )

    def initialize(self):
        if len(sys.argv) > 1:
            path = os.path.expanduser(sys.argv[1])

            if os.path.isdir(path):
                # Open directory in the file browser.
                self.browser.current_path = path
                self.browser.refresh()

            elif os.path.exists(path):
                # Existing file.
                open_editor_file(self.state, self.selectionState, path)
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

    def handle_refresh(self, key):
        if key != "CTRL_R":
            return False

        # TODO the following code must be refactored
        if self.state.active_tab_index < len(self.state.open_tabs):
            tab = self.state.open_tabs[self.state.active_tab_index]
            if tab is not None:
                tab.doc_lines = load_file(tab.path) or [""]
                self.state.document = tab

        resize_layout(self.state, self.browser)
        clear()
        redraw_all(self.state, self.selectionState, self.browser)

        sys.stdout.flush()
        self.prev_key = key

        return True

    def handle_global_shortcuts(self, key):
        if key == "CTRL_P" and (self.mode == MODE.EDIT or self.mode == MODE.LOG):
            self.mode = MODE.EDIT if self.mode == MODE.LOG else MODE.LOG
            clear()

            if self.mode == MODE.EDIT:
                draw_status_line(self.state, self.browser)
                initial_set(self.state, self.selectionState)
                draw_file_browser(self.browser)
                print(end="")
                sys.stdout.flush()
            else:
                print("DEBUG MODE")

            self.prev_key = key
            return True

        if key in ("ALT+RIGHT", "CTRL+UP", "CTRL+LEFT", "CTRL+DOWN"):
            if key == "ALT+RIGHT":
                self.mode = MODE.TAB_BROWSER if self.mode == MODE.FILE_BROWSER else MODE.EDIT if self.mode == MODE.TAB_BROWSER else MODE.FILE_BROWSER
            elif key == "CTRL+UP":
                self.mode = MODE.TAB_BROWSER
            elif key == "CTRL+DOWN":
                self.mode = MODE.EDIT
            elif key == "CTRL+LEFT":
                self.mode = MODE.FILE_BROWSER

            clear()
            redraw_all(self.state, self.selectionState, self.browser)
            self.prev_key = key
            return True

        return False

    def run(self):
        self.initialize()

        while True:
            key = read_sequence()

            if self.handle_refresh(key) or self.handle_global_shortcuts(key):
                continue

            if self.mode == MODE.LOG:
                if handle_log_mode(key, self.prev_key):
                    break

                self.prev_key = key
                continue

            if self.mode == MODE.MODAL:
                should_break, self.mode, self.modal_payload = handle_modal_mode(
                    key,
                    self.mode,
                    self.modal_payload,
                    self.state,
                    self.selectionState,
                    self.browser,
                )

                if should_break:
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
                    self.mode = MODE.EDIT

                draw_tab_panel(self.state)
                sys.stdout.flush()
                print(end="")
                self.prev_key = key
                continue

            if self.mode == MODE.EDIT:
                self.mode, self.modal_payload = handle_edit_mode(
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
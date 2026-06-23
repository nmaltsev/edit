import sys
import os
from enum import Enum
from .utils.kbd import get_key, clear
from .utils.layout import draw_status_line, redraw_all, resize_layout, prompt_text, find_files, show_find_results, confirm_delete, reset_editor, open_editor_file
from .file_helpers import load_file, save_file, rm_path
from .state import EditorState, SelectionState, FileBrowserState
from .editor_helpers import print_status, initial_set
from .process_editor_keys import process_editor_keys
from .file_browser_helpers import draw_file_browser, process_file_browser_key
from .utils.ui import trim_path, trim_name


class MODE(Enum):
    EDIT = 0
    LOG = 1
    MODAL = 2
    FILE_BROWSER = 3
    TAB_BROWSER = 4
    TERM = 5


class Application:
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

    def initialize(self):
        if len(sys.argv) > 1:
            path = sys.argv[1]

            try:
                if os.stat(path)[0] & 0x4000:
                    # If the path is a directory
                    self.browser.current_path = path
                    self.browser.refresh()
                else:
                    open_editor_file(
                        self.state,
                        self.selectionState,
                        path,
                    )
                    self.mode = MODE.EDIT

            except FileNotFoundError:
                self.browser.current_path = os.getcwd()

        clear()
        draw_status_line(self.state, self.browser)

        if self.state.file_path:
            initial_set(self.state, self.selectionState)

        draw_file_browser(self.browser)
        print(end="")
        sys.stdout.flush()

    def redraw(self):
        clear()
        redraw_all(
            self.state,
            self.selectionState,
            self.browser,
        )

    def switch_to_file_browser(self):
        self.mode = MODE.FILE_BROWSER
        draw_status_line(self.state, self.browser)
        draw_file_browser(self.browser)
        sys.stdout.flush()

    def switch_to_edit(self):
        self.mode = MODE.EDIT

        draw_status_line(
            self.state,
            self.browser,
        )

        if self.state.file_path:
            initial_set(
                self.state,
                self.selectionState,
            )

        draw_file_browser(
            self.browser,
        )

        sys.stdout.flush()

    def handle_refresh(self, key):
        if key != "CTRL_R":
            return False

        # TODO process_redraw()
        resize_layout(
            self.state,
            self.browser,
        )

        clear()
        redraw_all(
            self.state,
            self.selectionState,
            self.browser,
        )

        sys.stdout.flush()

        self.prev_key = key
        return True

    def handle_global_shortcuts(self, key):
        if key == "CTRL_P" and (self.mode == MODE.EDIT or self.mode == MODE.LOG):
            self.mode = MODE.EDIT if self.mode == MODE.LOG else MODE.LOG

            #  TODO process_
            clear()

            if self.mode == MODE.EDIT:
                draw_status_line(
                    self.state,
                    self.browser,
                )

                initial_set(
                    self.state,
                    self.selectionState,
                )

                draw_file_browser(
                    self.browser,
                )

                print(end="")
                sys.stdout.flush()
            else:
                print("DEBUG MODE")

            self.prev_key = key
            return True

        if key == "ALT+RIGHT":
            if self.mode == MODE.FILE_BROWSER:
                self.switch_to_edit()
            else:
                self.switch_to_file_browser()

            self.prev_key = key
            return True

        return False

    def handle_log_mode(self, key):
        print(f"{key=}")

        if key == "CTRL_T" and self.prev_key == "CTRL_T":
            size = os.get_terminal_size()
            print(f"columns: {size.columns} lines: {size.lines}")

        if key == "CTRL_W":
            clear()

        self.prev_key = key

    def handle_modal_mode(self, key):
        if self.modal_payload:
            action = self.modal_payload.get("action")

            if action == "CLOSE_EDITOR":
                if key == "y":
                    if self.state.file_path and self.state.file_path != "Untitled":
                        save_file(
                            self.state.file_path,
                            self.state.doc_lines,
                        )

                reset_editor(
                    self.state,
                    self.selectionState,
                )

                self.mode = MODE.FILE_BROWSER

                clear()
                redraw_all(
                    self.state,
                    self.selectionState,
                    self.browser,
                )

                self.prev_key = key
                return

            if action == "EXIT_APP":
                if key == "y":
                    clear()
                    raise SystemExit

                self.mode = MODE.FILE_BROWSER
                self.modal_payload = None

                clear()
                redraw_all(
                    self.state,
                    self.selectionState,
                    self.browser,
                )

                self.prev_key = key
                return

        self.prev_key = key

    def handle_save_as(self, key):
        if key != "ALT+S":
            return False

        target = prompt_text(
            "Save as file name"
        )

        if target:
            try:
                save_file(
                    target,
                    self.state.doc_lines,
                )

                self.state.file_path = target
                self.state.modified = False

            except Exception as ex:
                clear()
                redraw_all(
                    self.state,
                    self.selectionState,
                    self.browser,
                )

                print_status(
                    self.state,
                    str(ex),
                )

                self.prev_key = key
                return True

        clear()
        redraw_all(
            self.state,
            self.selectionState,
            self.browser,
        )

        self.prev_key = key
        return True

    def handle_save(self, key):
        if key != "CTRL_S":
            return False

        if (
            not self.state.file_path
            or self.state.file_path == "Untitled"
        ):
            target = prompt_text(
                "Save as file name"
            )

            if not target:
                clear()
                redraw_all(
                    self.state,
                    self.selectionState,
                    self.browser,
                )

                self.prev_key = key
                return True

            self.state.file_path = target

        save_file(
            self.state.file_path,
            self.state.doc_lines,
        )

        self.state.modified = False
        redraw_all(
            self.state,
            self.selectionState,
            self.browser,
        )

        self.prev_key = key
        return True

    def handle_close_editor(self, key):
        if key != "CTRL_Q":
            return False

        if self.state.modified:
            self.mode = MODE.MODAL

            self.modal_payload = {
                "action": "CLOSE_EDITOR",
            }

            print_status(
                self.state,
                "Save before close? y/n",
            )

            self.prev_key = key
            return True

        reset_editor(
            self.state,
            self.selectionState,
        )

        self.mode = MODE.FILE_BROWSER

        clear()
        redraw_all(
            self.state,
            self.selectionState,
            self.browser,
        )

        self.prev_key = key
        return True

    def handle_edit_mode(self, key):
        if self.handle_close_editor(key):
            return

        if self.handle_save_as(key):
            return

        if self.handle_save(key):
            return

        draw_status_line(
            self.state,
            self.browser,
        )

        draw_file_browser(
            self.browser,
        )

        process_editor_keys(
            key,
            self.prev_key,
            self.state,
            self.selectionState,
        )

        self.prev_key = key

    def _create_new_file(self, key):
        reset_editor(
            self.state,
            self.selectionState,
        )

        self.state.file_path = "Untitled"

        self.mode = MODE.EDIT

        clear()

        draw_status_line(
            self.state,
            self.browser,
        )

        initial_set(
            self.state,
            self.selectionState,
        )

        draw_file_browser(
            self.browser,
        )

        sys.stdout.flush()

        self.prev_key = key

    def _open_file(self, path, key):
        open_editor_file(
            self.state,
            self.selectionState,
            path,
        )

        self.mode = MODE.EDIT

        draw_status_line(
            self.state,
            self.browser,
        )

        initial_set(
            self.state,
            self.selectionState,
        )

        draw_file_browser(
            self.browser,
        )

        sys.stdout.flush()

        self.prev_key = key

    def _delete_path(self, path, key):
        if confirm_delete(path):
            try:
                rm_path(path)
            except Exception as ex:
                clear()
                redraw_all(
                    self.state,
                    self.selectionState,
                    self.browser,
                )
                print_status(
                    self.state,
                    str(ex),
                )
                self.prev_key = key
                return

        self.browser.refresh()

        clear()
        redraw_all(
            self.state,
            self.selectionState,
            self.browser,
        )

        self.prev_key = key

    def _create_directory(self, path, key):
        directory_name = prompt_text(
            "Enter the name of the directory and press enter"
        )

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
                    self.state,
                    self.selectionState,
                    self.browser,
                )
                print_status(
                    self.state,
                    str(ex),
                )
                self.prev_key = key
                return

        self.browser.refresh()

        clear()
        redraw_all(
            self.state,
            self.selectionState,
            self.browser,
        )

        sys.stdout.flush()
        self.prev_key = key

    def _create_file(self, path, key):
        filename = prompt_text(
            "Enter the name of the file and press enter"
        )

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
                redraw_all(
                    self.state,
                    self.selectionState,
                    self.browser,
                )
                print_status(
                    self.state,
                    str(ex),
                )
                self.prev_key = key
                return

        self.browser.refresh()

        clear()
        redraw_all(
            self.state,
            self.selectionState,
            self.browser,
        )

        self.prev_key = key

    def _rename_path(self, path, key):
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
                    self.state,
                    self.selectionState,
                    self.browser,
                )
                print_status(
                    self.state,
                    str(ex),
                )
                self.prev_key = key
                return

        self.browser.refresh()

        clear()
        redraw_all(
            self.state,
            self.selectionState,
            self.browser,
        )

        self.prev_key = key

    def _find_by_filename(self, path, key):
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
            self.state,
            self.selectionState,
            self.browser,
        )

        self.prev_key = key

    def handle_file_browser_action(self, action, path, key):
        if action == "OPEN_FILE":
            self._open_file(path, key)
        elif action == "DELETE":
            self._delete_path(path, key)
        elif action == "CREATE_DIR":
            self._create_directory(path, key)
        elif action == "CREATE_FILE":
            self._create_file(path, key)
        elif action == "RENAME":
            self._rename_path(path, key)
        elif action == "FIND_BY_FNAME":
            self._find_by_filename(path, key)

    def handle_file_browser_mode(self, key):
        if key == "CTRL_Q":
            if self.prev_key == "CTRL_Q":
                clear()
                raise SystemExit

            print_status(
                self.state,
                "Press CTRL_Q again to exit",
            )

            self.prev_key = key
            return

        if key == "ALT+N":
            self._create_new_file(key)
            return

        result = process_file_browser_key(
            key,
            self.browser,
            self.state,
        )

        draw_status_line(
            self.state,
            self.browser,
        )

        draw_file_browser(
            self.browser,
        )

        sys.stdout.flush()

        if result:
            action, path = result
            self.handle_file_browser_action(
                action,
                path,
                key,
            )
            return

        draw_status_line(
            self.state,
            self.browser,
        )

        draw_file_browser(
            self.browser,
        )

        self.prev_key = key

    def run(self):
        self.initialize()

        while True:
            key = get_key()

            try:
                if self.handle_refresh(key):
                    continue

                if self.handle_global_shortcuts(key):
                    continue

                if self.mode == MODE.LOG:
                    self.handle_log_mode(key)
                    continue

                if self.mode == MODE.MODAL:
                    self.handle_modal_mode(key)
                    continue

                if self.mode == MODE.EDIT:
                    self.handle_edit_mode(key)
                    continue

                if self.mode == MODE.FILE_BROWSER:
                    self.handle_file_browser_mode(key)
                    continue

                self.prev_key = key

            except SystemExit:
                break


def main(use_tab: bool = False, tab_size: int = 2):
    Application(
        use_tab=use_tab,
        tab_size=tab_size,
    ).run()


if __name__ == "__main__":
    main()
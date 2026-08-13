import os
from typing import Optional

Position = tuple[int, int]

class DocumentState:
    def __init__(self, path=None, doc_lines=None, is_viewer=False):
        self.path = path
        self.doc_lines = doc_lines or [""]
        self.cursor_offset = [0, 0]
        self.view_offset = 0
        self.modified = False
        self.is_viewer = is_viewer

    def get_selected_text(self, r:Optional[tuple[Position, Position]]) -> str:
        if not r:
            return ""

        (r1, c1), (r2, c2) = r
        if r1 == r2:
            return self.doc_lines[r1][c1:c2]

        out = [self.doc_lines[r1][c1:]]

        for y in range(r1 + 1, r2):
            out.append(self.doc_lines[y])

        out.append(self.doc_lines[r2][:c2])
        return "\n".join(out)

    def delete_selection(self, r:Optional[tuple[Position, Position]]) -> Position:
        (r1, c1), (r2, c2) = r
        
        if r1 == r2:
            line = self.doc_lines[r1]
            self.doc_lines[r1] = line[:c1] + line[c2:]
        else:
            first = self.doc_lines[r1][:c1]
            last = self.doc_lines[r2][c2:]

            self.doc_lines[r1] = first + last
            del self.doc_lines[r1 + 1:r2 + 1]

        return r1, c1
    
    def insert_text(self, row, col, text):
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        parts = text.split("\n")
        line = self.doc_lines[row]
        before = line[:col]
        after = line[col:]

        if len(parts) == 1:
            self.doc_lines[row] = before + text + after
            return row, col + len(text)

        self.doc_lines[row] = before + parts[0]
        insert_pos = row + 1

        for p in parts[1:-1]:
            self.doc_lines.insert(insert_pos, p)
            insert_pos += 1

        self.doc_lines.insert(insert_pos, parts[-1] + after)
        return insert_pos, len(parts[-1])

def _display_line(state, doc_y):
    return state.document.doc_lines[doc_y].expandtabs(state.tab_size)


def _display_to_doc_col(line, display_col, tab_size):
    """
    Convert visual column position to real document column.

    Tabs occupy one character in the document but multiple
    visual columns on screen.
    """
    visual = 0

    for doc_col, ch in enumerate(line):
        if ch == "\t":
            next_visual = visual + (tab_size - (visual % tab_size))
        else:
            next_visual = visual + 1

        if display_col < next_visual:
            return doc_col

        visual = next_visual

    return len(line)


def _doc_to_display_col(line, doc_col, tab_size):
    """
    Convert document column to visual column.
    """
    visual = 0

    for ch in line[:doc_col]:
        if ch == "\t":
            visual += tab_size - (visual % tab_size)
        else:
            visual += 1

    return visual



class EditorState:
    def __init__(self, use_tab: bool = False, tab_size: int = 2, view_box=(1, 1, 50, 20)):
        self.use_tab = use_tab
        self.tab_size = tab_size
        self.view_box = view_box  # (x,y,w,h) immutable

        self.document = DocumentState()

        self.open_tabs = []
        self.active_tab_index = -1

    def get_tab(self):
        if self.use_tab:
            return "\t"
        return " " * self.tab_size

    def get_active_document(self):
        if (self.active_tab_index > -1 and self.active_tab_index < len(self.open_tabs)):
            return self.open_tabs[self.active_tab_index]
        return None

    def save_active_tab_state(self):
        """
        No copying is required because EditorState.document references the
        active DocumentState instance stored in open_tabs.
        """
        if self.active_tab_index < 0 or self.active_tab_index >= len(self.open_tabs):
            return

        self.open_tabs[self.active_tab_index] = self.document

    def findExistingTabByPath(self, path: str):
        tab_index = None

        for index, document in enumerate(self.open_tabs):
            if document.path == path:
                tab_index = index
                break
        return tab_index

    def unindent_line(self, line:str):
        indent = self.get_tab()

        if indent == "\t":
            if line.startswith(indent):
                return line[1:]

            return line

        if line.startswith(indent):
            return line[len(indent):]

        if line.startswith("\t"):
            return line[1:]

        stripped = 0

        while (
            stripped < self.tab_size
            and stripped < len(line)
            and line[stripped] == " "
        ):
            stripped += 1

        return line[stripped:]
    
    def build_visual_lines(self):
        visual = []
        width = max(1, self.view_box[2])

        for doc_y, line in enumerate(self.document.doc_lines):
            expanded = line.expandtabs(self.tab_size)

            if expanded == "":
                visual.append((doc_y, 0, ""))
                continue

            start = 0

            while start < len(expanded):
                segment = expanded[start:start + width]
                visual.append((doc_y, start, segment))
                start += width

        return visual

class SelectionState:
    def __init__(self) -> None:
        self.active: bool = False
        self.anchor: Optional[Position] = None
        self.end: Optional[Position] = None
        self.in_progress: bool = False

    def normalize_selection(self) -> Optional[tuple[Position, Position]]:
        if self.anchor is None or self.end is None:
            return None

        a = self.anchor
        b = self.end

        if a <= b:
            return a, b

        return b, a

    def has_selection(self) -> bool:
        r = self.normalize_selection()

        if r is None:
            return False

        a, b = r
        return a != b

    def clear_selection(self) -> None:
        self.active = False
        self.anchor = None
        self.end = None
        self.in_progress = False

    def begin_selection(self, row: int, col: int) -> None:
        if not self.active:
            self.active = True
            self.anchor = (row, col)

        self.end = (row, col)
        self.in_progress = True

    def update_selection(self, row: int, col: int) -> None:
        self.end = (row, col)

    def finalize_selection(self) -> None:
        self.in_progress = False

class FileBrowserState:
    def __init__(self, start_path=None, view_box=(0, 0, 30, 20)):
        self.current_path = os.path.abspath(start_path or os.getcwd())
        self.view_box = view_box
        self.items = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.refresh()

    def refresh(self):
        dirs = []
        files = []

        for name in os.listdir(self.current_path):
            full = os.path.join(self.current_path, name)

            if os.path.isdir(full):
                dirs.append(name)
            else:
                files.append(name)

        dirs.sort()
        files.sort()

        self.items = [".."] + dirs + files

        if self.selected_index >= len(self.items):
            self.selected_index = max(0, len(self.items) - 1)

    def current_item(self):
        if not self.items:
            return None

        return self.items[self.selected_index]

    def current_full_path(self):
        item = self.current_item()

        if item == "..":
            return os.path.dirname(self.current_path)

        return os.path.join(self.current_path, item)
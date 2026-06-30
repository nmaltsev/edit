import sys

from .utils.kbd import clear, move_cursor
from .utils.text import fill
from .syntax_highlighting import render_line


def get_selected_text(state, selectionState):
    document = state.document
    r = selectionState.normalize_selection()

    if not r:
        return ""

    (r1, c1), (r2, c2) = r
    lines = document.doc_lines

    if r1 == r2:
        return lines[r1][c1:c2]

    out = [lines[r1][c1:]]

    for y in range(r1 + 1, r2):
        out.append(lines[y])

    out.append(lines[r2][:c2])

    return "\n".join(out)


def delete_selection(state, selectionState):
    document = state.document
    r = selectionState.normalize_selection()

    if not r:
        return None

    (r1, c1), (r2, c2) = r
    doc_lines = document.doc_lines

    if r1 == r2:
        line = doc_lines[r1]
        doc_lines[r1] = line[:c1] + line[c2:]
    else:
        first = doc_lines[r1][:c1]
        last = doc_lines[r2][c2:]

        doc_lines[r1] = first + last
        del doc_lines[r1 + 1:r2 + 1]

    selectionState.clear_selection()

    return r1, c1


def insert_text(state, row, col, text):
    document = state.document

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    parts = text.split("\n")

    doc_lines = document.doc_lines
    line = doc_lines[row]

    before = line[:col]
    after = line[col:]

    if len(parts) == 1:
        doc_lines[row] = before + text + after
        return row, col + len(text)

    doc_lines[row] = before + parts[0]

    insert_pos = row + 1

    for p in parts[1:-1]:
        doc_lines.insert(insert_pos, p)
        insert_pos += 1

    doc_lines.insert(insert_pos, parts[-1] + after)

    return insert_pos, len(parts[-1])


def replace_selection(state, selectionState, text):
    pos = delete_selection(state, selectionState)

    if pos is None:
        return None

    row, col = pos

    return insert_text(state, row, col, text)


def _unindent_line(line, state):
    indent = state.get_tab()

    if indent == "\t":
        if line.startswith("\t"):
            return line[1:]

        return line

    if line.startswith(indent):
        return line[len(indent):]

    if line.startswith("\t"):
        return line[1:]

    stripped = 0

    while (
        stripped < state.tab_size
        and stripped < len(line)
        and line[stripped] == " "
    ):
        stripped += 1

    return line[stripped:]


def shift_selected_lines(state, selectionState, direction):
    document = state.document
    r = selectionState.normalize_selection()

    if not r:
        return None

    (r1, c1), (r2, c2) = r

    indent = state.get_tab()

    if direction > 0:
        for y in range(r1, r2 + 1):
            document.doc_lines[y] = indent + document.doc_lines[y]
    else:
        for y in range(r1, r2 + 1):
            document.doc_lines[y] = _unindent_line(
                document.doc_lines[y],
                state,
            )

    return r1, c1


def _expand_tabs(text, tab_size):
    return text.expandtabs(tab_size)


def build_visual_lines(state):
    document = state.document

    visual = []
    width = max(1, state.view_box[2])
    tab_size = state.tab_size

    for doc_y, line in enumerate(document.doc_lines):
        expanded = _expand_tabs(
            line,
            tab_size,
        )

        if expanded == "":
            visual.append((doc_y, 0, ""))
            continue

        start = 0

        while start < len(expanded):
            segment = expanded[start:start + width]
            visual.append((doc_y, start, segment))
            start += width

    return visual


def find_visual_index(visual, doc_y, real_x):
    if not visual:
        return 0

    for i, (dy, start, seg) in enumerate(visual):
        if dy == doc_y and start <= real_x <= start + len(seg):
            return i

    return len(visual) - 1


def move_page(state, doc_y, real_x, direction):
    document = state.document

    visual = build_visual_lines(state)

    if not visual:
        return 0, 0, visual

    current_vis_idx = find_visual_index(
        visual,
        doc_y,
        real_x,
    )

    _, current_start, _ = visual[current_vis_idx]
    cx = real_x - current_start

    target_vis_idx = current_vis_idx + (direction * state.view_box[3])

    if target_vis_idx < 0:
        target_vis_idx = 0

    if target_vis_idx >= len(visual):
        target_vis_idx = len(visual) - 1

    target_dy, target_start, _ = visual[target_vis_idx]

    target_real_x = min(
        target_start + cx,
        len(
            _expand_tabs(
                document.doc_lines[target_dy],
                state.tab_size,
            )
        ),
    )

    return target_dy, target_real_x, visual

def fill_view_box(state, view_box, visual_lines, cursor=None):
    document = state.document

    for i in range(view_box[3]):
        move_cursor(
            view_box[0],
            view_box[1] + i,
        )

        idx = document.view_offset + i

        if idx < len(visual_lines):
            _, _, text = visual_lines[idx]
        else:
            text = ""

        cursor_text = text

        if cursor and i == cursor[1]:
            cx = cursor[0]

            if cx >= len(cursor_text):
                cursor_text = cursor_text + "_"
            else:
                cursor_text = (
                    cursor_text[:cx]
                    + "_"
                    + cursor_text[cx:]
                )

        rendered = render_line(
            document.path,
            cursor_text,
        )

        print(
            fill(
                rendered,
                view_box[2],
            ),
            end="",
        )

    sys.stdout.flush()


def get_status(selectionState, doc_y, real_x, ch, path):
    """
    Returns the status bar content for Edit mode.
    The status bar displays:
    - the current file name
    - an asterisk (*) if the file has unsaved changes
    - the current cursor position or active selection location
    - the character at the current cursor position
    """

    if selectionState.has_selection():
        (r1, c1), (r2, c2) = selectionState.normalize_selection()
        return f"({r1 + 1},{c1 + 1},{r2 + 1},{c2 + 1}) {path}"

    return f"({doc_y + 1}:{real_x + 1}) {repr(ch)} {path}"


def print_status(state, message):
    y = state.view_box[1] + state.view_box[3]

    move_cursor(
        state.view_box[0],
        y,
    )

    print(
        fill(
            message,
            state.view_box[2],
        ),
        end="",
    )

    sys.stdout.flush()


def initial_set(state, selectionState):
    # clear()
    document = state.document

    visual = build_visual_lines(state)

    fill_view_box(
        state,
        state.view_box,
        visual,
        cursor=document.cursor_offset,
    )

    vis_idx = document.view_offset + document.cursor_offset[1]

    if vis_idx >= len(visual):
        vis_idx = len(visual) - 1

    doc_y, start_idx, _ = visual[vis_idx]
    real_x = start_idx + document.cursor_offset[0]

    print_status(
        state,
        get_status(
            selectionState,
            doc_y,
            real_x,
            "",
            document.path,
        ),
    )
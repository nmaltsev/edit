import sys

from .utils.terminal import clear, move_cursor
from .utils.text import fill
from .syntax_highlighting import render_line


def delete_selection(document, selectionState):
    r = selectionState.normalize_selection()

    if not r:
        return None

    selection_start_pos = document.delete_selection(r)
    selectionState.clear_selection()
    return selection_start_pos


def replace_selection(state, selectionState, text):
    pos = delete_selection(state.document, selectionState)

    if pos is None:
        return None

    row, col = pos

    return state.document.insert_text(row, col, text)

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
            document.doc_lines[y] = state.unindent_line(document.doc_lines[y])

    return r1, c1


def find_visual_index(visual, doc_y, real_x):
    if not visual:
        return 0

    for i, (dy, start, seg) in enumerate(visual):
        if dy == doc_y and start <= real_x <= start + len(seg):
            return i

    return len(visual) - 1


def move_page(state, doc_y, real_x, direction):
    document = state.document

    visual = state.build_visual_lines()

    if not visual:
        return 0, 0, visual

    current_vis_idx = find_visual_index(visual, doc_y, real_x)

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
        len(document.doc_lines[target_dy].expandtabs(state.tab_size)),
    )

    return target_dy, target_real_x, visual

def fill_view_box(state, view_box, visual_lines, cursor=None):
    document = state.document

    for i in range(view_box[3]):
        move_cursor(view_box[0], view_box[1] + i)
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
                cursor_text = cursor_text[:cx] + "_" + cursor_text[cx:]

        rendered = render_line(document.path, cursor_text)
        print(fill(rendered, view_box[2]), end="")
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

    move_cursor(state.view_box[0], y)
    print(fill(message, state.view_box[2]), end="")
    sys.stdout.flush()


def initial_set(state, selectionState):
    document = state.document
    visual = state.build_visual_lines()
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
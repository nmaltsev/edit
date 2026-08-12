from dataclasses import dataclass
from .editor_helpers import ( 
    delete_selection,
    replace_selection,
    shift_selected_lines,
    move_page,
    fill_view_box,
    get_status,
    print_status,
)
from .clipboard import copy_to_clipboard, paste_from_clipboard
from .state import _display_line, _display_to_doc_col, _doc_to_display_col

@dataclass
class EditorResult:
    doc_y: int
    real_x: int
    visual: list
    exit_editor: bool = False


def process_editor_keys(key, prev_key, state, selectionState):
    document = state.document

    visual = state.build_visual_lines()

    if not visual:
        visual = [(0, 0, "")]

    cx, cy = document.cursor_offset
    vis_idx = document.view_offset + cy

    if vis_idx >= len(visual):
        vis_idx = len(visual) - 1

    doc_y, start_idx, segment = visual[vis_idx]
    line = document.doc_lines[doc_y]
    display_x = start_idx + cx
    doc_x = _display_to_doc_col(line, display_x, state.tab_size)
    real_x = doc_x

    shift_move = key in ("SHIFT+LEFT", "SHIFT+RIGHT", "SHIFT+UP", "SHIFT+DOWN", "SHIFT+PAGE_DOWN", "SHIFT+PAGE_UP", "SHIFT+HOME", "SHIFT+END", "HOME", "END", "PAGE_UP", "PAGE_DOWN")

    # --------------------------------------------------
    # Selection begin/end
    # --------------------------------------------------
    if shift_move:
        if not selectionState.in_progress:
            selectionState.begin_selection(doc_y, real_x)
    else:
        if selectionState.in_progress:
            selectionState.finalize_selection()

    # --------------------------------------------------
    # Select All
    # --------------------------------------------------
    if key == "CTRL_A":
        if not document.doc_lines:
            document.doc_lines = [""]

        last_row = len(document.doc_lines) - 1
        last_col = len(document.doc_lines[last_row])

        selectionState.clear_selection()
        selectionState.begin_selection(0, 0)
        selectionState.update_selection(last_row, last_col)
        selectionState.finalize_selection()

    # --------------------------------------------------
    # Shift selected block
    # --------------------------------------------------
    elif selectionState.has_selection() and key in ("TAB", "SHIFT+TAB"):
        if key == "TAB":
            shift_selected_lines(state, selectionState, 1)
        else:
            shift_selected_lines(state, selectionState, -1)
        document.modified = True

    # --------------------------------------------------
    # Selection operations
    # --------------------------------------------------
    elif selectionState.has_selection():
        selection_consumed = False

        if key == "CTRL_C":
            copy_to_clipboard(state.document.get_selected_text(selectionState.normalize_selection()))
            selection_consumed = True
        elif key == "CTRL_X":
            copy_to_clipboard(state.document.get_selected_text(selectionState.normalize_selection()))
            pos = delete_selection(state.document, selectionState)

            if pos:
                doc_y, real_x = pos
                document.modified = True

            selection_consumed = True
        elif key in ("DEL", "BACKSPACE"):
            pos = delete_selection(state.document, selectionState)

            if pos:
                doc_y, real_x = pos
                document.modified = True

            selection_consumed = True
        elif key == "CTRL_V":
            text = paste_from_clipboard()
            pos = replace_selection(state, selectionState, text)

            if pos:
                doc_y, real_x = pos
                document.modified = True

            selection_consumed = True
        elif (
            len(key) == 1
            and not key.startswith("CTRL_")
            and not key.startswith("ALT+")
            and not key.startswith("SHIFT+")
        ):
            pos = replace_selection(state, selectionState, key)

            if pos:
                doc_y, real_x = pos
                document.modified = True

            selection_consumed = True

        elif not shift_move:
            selectionState.clear_selection()

        if selection_consumed:
            visual = state.build_visual_lines()

            if not visual:
                visual = [(0, 0, "")]

            display_x = _doc_to_display_col(
                document.doc_lines[doc_y],
                real_x,
                state.tab_size,
            )

            new_vis_idx = 0

            for i, (dy, start, seg) in enumerate(visual):
                if dy == doc_y and start <= display_x <= start + len(seg):
                    new_vis_idx = i
                    break

            _, start, _ = visual[new_vis_idx]

            cx = display_x - start
            cy = new_vis_idx - document.view_offset

            if cy < 0:
                document.view_offset = new_vis_idx
                cy = 0

            elif cy >= state.view_box[3]:
                document.view_offset = new_vis_idx - state.view_box[3] + 1
                cy = state.view_box[3] - 1

            document.cursor_offset = [cx, cy]
            fill_view_box(
                state,
                state.view_box,
                visual,
                cursor=(cx, cy),
            )
            ch = ""

            if (
                doc_y < len(document.doc_lines)
                and real_x < len(document.doc_lines[doc_y])
            ):
                ch = document.doc_lines[doc_y][real_x]

            print_status(
                state,
                get_status(
                    selectionState,
                    doc_y,
                    real_x,
                    ch,
                    document.path + ("*" if document.modified else "") if document.path else "",
                ),
            )

            return EditorResult(doc_y=doc_y, real_x=real_x, visual=visual)

    # --------------------------------------------------
    # Paste
    # --------------------------------------------------
    if key == "CTRL_V":
        text = paste_from_clipboard()

        if selectionState.has_selection():
            pos = replace_selection(state, selectionState, text)

            if pos:
                doc_y, real_x = pos
                document.modified = True
        else:
            doc_y, real_x = state.document.insert_text(doc_y, real_x, text)
            document.modified = True

    # --------------------------------------------------
    # Insert tab
    # --------------------------------------------------
    elif key == "TAB":
        if not selectionState.has_selection():
            doc_y, real_x = state.document.insert_text(doc_y, real_x, state.get_tab())
            document.modified = True

    # --------------------------------------------------
    # Printable chars
    # --------------------------------------------------
    elif len(key) == 1:
        line = document.doc_lines[doc_y]
        document.doc_lines[doc_y] = line[:real_x] + key + line[real_x:]
        real_x += 1
        document.modified = True

    # --------------------------------------------------
    # Enter
    # --------------------------------------------------
    elif key == "ENTER":
        line = document.doc_lines[doc_y]
        new_line = line[real_x:]
        document.doc_lines[doc_y] = line[:real_x]
        document.doc_lines.insert(doc_y + 1, new_line)
        doc_y += 1
        real_x = 0
        document.modified = True

    # --------------------------------------------------
    # Backspace
    # --------------------------------------------------
    elif key == "BACKSPACE":
        line = document.doc_lines[doc_y]

        if real_x > 0:
            document.doc_lines[doc_y] = line[:real_x - 1] + line[real_x:]
            real_x -= 1
        elif doc_y > 0:
            prev_line = document.doc_lines[doc_y - 1]
            real_x = len(prev_line)
            document.doc_lines[doc_y - 1] = prev_line + line
            document.doc_lines.pop(doc_y)
            doc_y -= 1

        document.modified = True

    # --------------------------------------------------
    # Delete
    # --------------------------------------------------
    elif key == "DEL":
        line = document.doc_lines[doc_y]

        if real_x < len(line):
            document.doc_lines[doc_y] = line[:real_x] + line[real_x + 1:]
        elif doc_y < len(document.doc_lines) - 1:
            document.doc_lines[doc_y] += document.doc_lines[doc_y + 1]
            document.doc_lines.pop(doc_y + 1)

        document.modified = True

    # --------------------------------------------------
    # Navigation
    # --------------------------------------------------
    elif key in ("LEFT", "SHIFT+LEFT"):
        if real_x > 0:
            real_x -= 1
        elif doc_y > 0:
            doc_y -= 1
            real_x = len(document.doc_lines[doc_y])

    elif key in ("RIGHT", "SHIFT+RIGHT"):
        if real_x < len(document.doc_lines[doc_y]):
            real_x += 1
        elif doc_y < len(document.doc_lines) - 1:
            doc_y += 1
            real_x = 0

    elif key in ("UP", "SHIFT+UP"):
        if doc_y > 0:
            target_display_x = _doc_to_display_col(
                document.doc_lines[doc_y],
                real_x,
                state.tab_size,
            )

            doc_y -= 1

            real_x = _display_to_doc_col(
                document.doc_lines[doc_y],
                target_display_x,
                state.tab_size,
            )

    elif key in ("DOWN", "SHIFT+DOWN"):
        if doc_y < len(document.doc_lines) - 1:
            target_display_x = _doc_to_display_col(
                document.doc_lines[doc_y],
                real_x,
                state.tab_size,
            )

            doc_y += 1

            real_x = _display_to_doc_col(
                document.doc_lines[doc_y],
                target_display_x,
                state.tab_size,
            )

    elif key in ("HOME", "SHIFT+HOME"):
        real_x = 0

    elif key in ("END", "SHIFT+END"):
        real_x = len(document.doc_lines[doc_y])

    elif key in ("PAGE_DOWN", "ALT+PAGE_DOWN"):
        doc_y, real_x, visual = move_page(state, doc_y, real_x, 1)

    elif key in ("PAGE_UP", "ALT+PAGE_UP"):
        doc_y, real_x, visual = move_page(state, doc_y, real_x, -1)
    # --------------------------------------------------
    # Selection update
    # --------------------------------------------------
    if shift_move:
        selectionState.update_selection(doc_y, real_x)

    # --------------------------------------------------
    # Rebuild screen
    # --------------------------------------------------
    visual = state.build_visual_lines()
    display_x = _doc_to_display_col(document.doc_lines[doc_y], real_x, state.tab_size)
    new_vis_idx = 0

    for i, (dy, start, seg) in enumerate(visual):
        if dy == doc_y and start <= display_x <= start + len(seg):
            new_vis_idx = i
            break

    _, start, _ = visual[new_vis_idx]

    cx = display_x - start
    cy = new_vis_idx - document.view_offset

    if cy < 0:
        document.view_offset = new_vis_idx
        cy = 0

    elif cy >= state.view_box[3]:
        document.view_offset = new_vis_idx - state.view_box[3] + 1
        cy = state.view_box[3] - 1

    document.cursor_offset = [cx, cy]
    fill_view_box(state, state.view_box, visual, cursor=(cx, cy))
    ch = ""

    if (
        doc_y < len(document.doc_lines)
        and real_x < len(document.doc_lines[doc_y])
    ):
        ch = document.doc_lines[doc_y][real_x]

    print_status(
        state,
        get_status(
            selectionState,
            doc_y,
            real_x,
            ch,
            document.path + ("*" if document.modified else "") if document.path is not None else "",
        ),
    )

    return EditorResult(doc_y=doc_y, real_x=real_x, visual=visual)
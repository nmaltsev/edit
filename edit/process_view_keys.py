# ./edit/process_view_keys.py
from dataclasses import dataclass
from .editor_helpers import (
    move_page,
    fill_view_box,
    get_status,
    print_status,
)
from .clipboard import copy_to_clipboard
from .state import _display_to_doc_col, _doc_to_display_col


@dataclass
class ViewResult:
    doc_y: int
    real_x: int
    visual: list


def process_view_keys(key, prev_key, state, selectionState):
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

    shift_move = key in (
        "SHIFT+LEFT", "SHIFT+RIGHT", "SHIFT+UP", "SHIFT+DOWN",
        "SHIFT+PAGE_DOWN", "SHIFT+PAGE_UP", "SHIFT+HOME", "SHIFT+END",
        "HOME", "END", "PAGE_UP", "PAGE_DOWN",
    )

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
    # Selection operations (copy only)
    # --------------------------------------------------
    elif selectionState.has_selection():
        selection_consumed = False

        if key == "CTRL_C":
            copy_to_clipboard(state.document.get_selected_text(selectionState.normalize_selection()))
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
                    document.path if document.path else "",
                ),
            )

            return ViewResult(doc_y=doc_y, real_x=real_x, visual=visual)

    # --------------------------------------------------
    # Navigation
    # --------------------------------------------------
    if key in ("LEFT", "SHIFT+LEFT"):
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

    elif key in ("PAGE_DOWN", "ALT+PAGE_DOWN", "SHIFT+PAGE_DOWN"):
        doc_y, real_x, visual = move_page(state, doc_y, real_x, 1)

    elif key in ("PAGE_UP", "ALT+PAGE_UP", "SHIFT+PAGE_UP"):
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

    elif cy >= state.view_box[3]-1: # -1 is a bottom odffset
        document.view_offset = new_vis_idx - (state.view_box[3]-1) + 1
        cy = state.view_box[3]-1 - 1

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
            document.path if document.path is not None else "",
        ),
    )

    return ViewResult(doc_y=doc_y, real_x=real_x, visual=visual)
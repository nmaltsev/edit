from __future__ import annotations

import bisect
import hashlib
import os
from datetime import datetime
from pathlib import Path


BLACKLISTED_DIRS = {"__pycache__", "node_modules"}


def hash(*args: str) -> str:
    """Return a stable hash suitable for a filename."""
    value = "".join(args).encode("utf-8")
    return hashlib.sha256(value).hexdigest()[:16]


def find_snippet(
    path: str | os.PathLike[str],
    pattern: str,
) -> list[tuple[int, int, int, int, int]]:
    """
    Find every occurrence of pattern in a text file.

    Returns:
        (
            line_number,
            match_offset,
            match_length,
            line_start_offset,
            line_length,
        )

    All offsets are character offsets.

    Multiple occurrences on the same line produce multiple tuples.
    """
    if not pattern:
        return []

    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        content = file.read()

    # Calculate the start offset of every line.
    line_starts = [0]

    for index, char in enumerate(content):
        if char == "\n":
            line_starts.append(index + 1)

    results = []

    offset = 0

    while True:
        match_offset = content.find(pattern, offset)

        if match_offset == -1:
            break

        # Find the line containing this occurrence.
        line_index = bisect.bisect_right(
            line_starts,
            match_offset,
        ) - 1

        line_number = line_index + 1
        line_start_offset = line_starts[line_index]

        # Find end of line.
        line_end_offset = content.find(
            "\n",
            line_start_offset,
        )

        if line_end_offset == -1:
            line_end_offset = len(content)

        line_length = line_end_offset - line_start_offset

        results.append(
            (
                line_number,
                match_offset,
                len(pattern),
                line_start_offset,
                line_length,
            )
        )

        # +1 means overlapping occurrences are also found.
        offset = match_offset + 1

    return results


def _iter_text_files(source: Path):
    """Recursively yield files while skipping excluded directories."""
    for root, dirs, files in os.walk(source):
        dirs[:] = [
            directory
            for directory in dirs
            if not directory.startswith(".")
            and directory not in BLACKLISTED_DIRS
        ]

        for filename in files:
            path = Path(root) / filename

            if path.is_file():
                yield path


def _read_text_file(path: Path) -> str | None:
    """
    Read a UTF-8 text file.

    Returns None for files that cannot be decoded/read.
    """
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def find_pattern(
    source: str | os.PathLike[str],
    pattern: str,
) -> str:
    """
    Search for pattern in a file or recursively in a directory.

    Results are written incrementally to:

        /tmp/find_results_<hash(source, pattern)>.txt

    Every occurrence is reported, including multiple occurrences
    on the same line.
    """
    source_path = Path(source)

    if not source_path.exists():
        raise FileNotFoundError(
            f"Source does not exist: {source}"
        )

    if not source_path.is_file() and not source_path.is_dir():
        raise ValueError(
            f"Source must be a file or directory: {source}"
        )

    result_path = Path(
        "/tmp"
        f"/find_results_{hash(str(source_path), pattern)}.txt"
    )

    started_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # Create/overwrite the result file for this search.
    with result_path.open("w", encoding="utf-8") as output:
        output.write(
            f"The search started: {started_at}\n\n"
        )
        output.write(
            f'{source_path} "{pattern}"\n\n'
        )

    if source_path.is_file():
        files = [source_path]
    else:
        files = _iter_text_files(source_path)

    result_number = 1

    for path in files:
        content = _read_text_file(path)

        if content is None:
            continue

        matches = find_snippet(path, pattern)

        if not matches:
            continue

        # Cache lines so that multiple matches on the same line
        # don't require recalculating the line text.
        lines: dict[int, str] = {}

        for (
            line_number,
            match_offset,
            match_length,
            line_start_offset,
            line_length,
        ) in matches:
            if line_number not in lines:
                lines[line_number] = content[
                    line_start_offset:
                    line_start_offset + line_length
                ]

            line = lines[line_number]

            with result_path.open(
                "a",
                encoding="utf-8",
            ) as output:
                output.write(
                    f"{result_number}. "
                    f"{path.name}:{line_number} "
                    f"{path.resolve()} "
                    f"[offset={match_offset}, "
                    f"length={match_length}]\n"
                )

                output.write(f"{line}\n\n")

            result_number += 1

    finished_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with result_path.open("a", encoding="utf-8") as output:
        output.write(
            f"The search end: {finished_at}\n"
        )

    return str(result_path)
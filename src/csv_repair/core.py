from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence


def repair(
    input_file: str | Path,
    output_file: str | Path,
    description_column: str = "DESCRIPTION",
) -> None:
    """Repair rows in an unquoted comma-separated file.

    The function expects a header row and reconstructs rows where the
    `description_column` contains unquoted commas. It does this by preserving
    columns before the description, preserving columns after the description
    from the row tail, and joining the remaining middle columns back into the
    description cell.
    """
    src = Path(input_file)
    dst = Path(output_file)

    with src.open("r", encoding="utf-8", newline="") as in_fh:
        lines = [line.rstrip("\r\n") for line in in_fh]

    if not lines:
        dst.write_text("", encoding="utf-8", newline="")
        return

    header_parts = _split_line(lines[0])
    expected_columns = len(header_parts)
    description_index = _index_of(header_parts, description_column)

    repaired_rows = [header_parts]

    for line in lines[1:]:
        if not line:
            continue

        parts = _split_line(line)
        fixed = _repair_parts(parts, expected_columns, description_index)
        repaired_rows.append(fixed)

    with dst.open("w", encoding="utf-8", newline="") as out_fh:
        writer = csv.writer(out_fh)
        writer.writerows(repaired_rows)


def _split_line(line: str) -> list[str]:
    return line.split(",")


def _index_of(header: Sequence[str], column_name: str) -> int:
    try:
        return header.index(column_name)
    except ValueError as exc:
        raise ValueError(f"Column '{column_name}' not found in header") from exc


def _repair_parts(parts: list[str], expected_columns: int, description_index: int) -> list[str]:
    if len(parts) == expected_columns:
        return parts

    if len(parts) < expected_columns:
        return parts + [""] * (expected_columns - len(parts))

    trailing_columns = expected_columns - description_index - 1
    left = parts[:description_index]

    if trailing_columns == 0:
        description = ",".join(parts[description_index:])
        return left + [description]

    right = parts[-trailing_columns:]
    middle = parts[description_index : len(parts) - trailing_columns]
    description = ",".join(middle)

    return left + [description] + right

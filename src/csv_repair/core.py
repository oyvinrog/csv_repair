from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence


class AmbiguousRowError(ValueError):
    """Raised when a row has multiple plausible repairs and no user choice is available."""


def repair(
    input_file: str | Path,
    output_file: str | Path,
    description_column: str | Sequence[str] = "DESCRIPTION",
) -> None:
    """Repair rows in an unquoted comma-separated file.

    The function expects a header row and reconstructs rows where the
    `description_column` contains unquoted commas. It preserves columns before
    the chosen text column, preserves columns after it from the row tail, and
    joins the remaining middle columns back into that text column.

    If multiple text columns are provided and a row is ambiguous, the function
    asks the user to choose the correct repair for that row.
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
    description_indices = _indices_of(header_parts, description_column)
    profiles = _column_profiles(lines[1:], expected_columns)

    repaired_rows = [header_parts]

    for line_number, line in enumerate(lines[1:], start=2):
        if not line:
            continue

        parts = _split_line(line)
        fixed = _repair_parts(
            parts,
            expected_columns,
            description_indices,
            profiles,
            line_number,
            line,
            header_parts,
        )
        repaired_rows.append(fixed)

    with dst.open("w", encoding="utf-8", newline="") as out_fh:
        writer = csv.writer(out_fh)
        writer.writerows(repaired_rows)


def _split_line(line: str) -> list[str]:
    return line.split(",")


def _indices_of(header: Sequence[str], column_name: str | Sequence[str]) -> list[int]:
    names = [column_name] if isinstance(column_name, str) else list(column_name)
    if not names:
        raise ValueError("At least one description column must be provided")

    indices: list[int] = []
    for name in names:
        try:
            indices.append(header.index(name))
        except ValueError as exc:
            raise ValueError(f"Column '{name}' not found in header") from exc

    return indices


def _column_profiles(lines: list[str], expected_columns: int) -> dict[int, dict[str, float]]:
    totals: dict[int, int] = {}
    counts: dict[int, int] = {}
    numeric_counts: dict[int, int] = {}
    non_empty_counts: dict[int, int] = {}

    for line in lines:
        if not line:
            continue
        parts = _split_line(line)
        if len(parts) != expected_columns:
            continue

        for idx, value in enumerate(parts):
            totals[idx] = totals.get(idx, 0) + len(value)
            counts[idx] = counts.get(idx, 0) + 1
            non_empty_counts[idx] = non_empty_counts.get(idx, 0) + (1 if value != "" else 0)
            numeric_counts[idx] = numeric_counts.get(idx, 0) + (1 if _is_number(value) else 0)

    profiles: dict[int, dict[str, float]] = {}
    for idx, count in counts.items():
        profiles[idx] = {
            "mean_length": totals[idx] / count,
            "numeric_ratio": numeric_counts[idx] / count,
            "non_empty_ratio": non_empty_counts[idx] / count,
        }

    return profiles


def _repair_parts(
    parts: list[str],
    expected_columns: int,
    description_indices: Sequence[int],
    profiles: dict[int, dict[str, float]],
    line_number: int,
    raw_line: str,
    header: Sequence[str],
) -> list[str]:
    if len(parts) == expected_columns:
        return parts

    if len(parts) < expected_columns:
        return parts + [""] * (expected_columns - len(parts))

    candidates: list[tuple[int, list[str], float]] = []
    for idx in description_indices:
        row = _repair_parts_at_index(parts, expected_columns, idx)
        score = _candidate_score(row, profiles, description_indices)
        candidates.append((idx, row, score))

    candidates.sort(key=lambda item: item[2])

    if len(candidates) == 1:
        return candidates[0][1]

    if _is_ambiguous(candidates):
        return _ask_user_to_choose(candidates, line_number, raw_line, header)

    return candidates[0][1]


def _repair_parts_at_index(parts: list[str], expected_columns: int, description_index: int) -> list[str]:
    trailing_columns = expected_columns - description_index - 1
    left = parts[:description_index]

    if trailing_columns == 0:
        description = ",".join(parts[description_index:])
        return left + [description]

    right = parts[-trailing_columns:]
    middle = parts[description_index : len(parts) - trailing_columns]
    description = ",".join(middle)

    return left + [description] + right


def _candidate_score(
    row: Sequence[str],
    profiles: dict[int, dict[str, float]],
    description_indices: Sequence[int],
) -> float:
    score = 0.0
    text_columns = set(description_indices)

    for idx, value in enumerate(row):
        profile = profiles.get(idx)
        if profile is None:
            continue

        mean_length = profile["mean_length"]
        length_penalty = abs(len(value) - mean_length) / (mean_length + 1.0)
        weight = 0.6 if idx in text_columns else 1.0
        score += weight * length_penalty

        if profile["numeric_ratio"] >= 0.8 and not _is_number(value):
            score += 5.0

        if profile["non_empty_ratio"] >= 0.95 and value == "":
            score += 2.0

    return score


def _is_ambiguous(candidates: Sequence[tuple[int, list[str], float]]) -> bool:
    if len(candidates) < 2:
        return False

    best_score = candidates[0][2]
    second_score = candidates[1][2]

    if abs(second_score - best_score) <= 0.1:
        return True

    if best_score == 0.0 and second_score == 0.0:
        return True

    if best_score > 0.0 and (second_score / best_score) <= 1.15:
        return True

    return False


def _ask_user_to_choose(
    candidates: Sequence[tuple[int, list[str], float]],
    line_number: int,
    raw_line: str,
    header: Sequence[str],
) -> list[str]:
    max_options = min(4, len(candidates))
    message_lines = [
        f"Ambiguous CSV row at line {line_number}.",
        f"Raw row: {raw_line}",
        "Choose the correct repair:",
    ]

    for i, (idx, row, score) in enumerate(candidates[:max_options], start=1):
        target_column = header[idx]
        preview = " | ".join(f"{name}={value}" for name, value in zip(header, row))
        message_lines.append(f"{i}. merge into '{target_column}' (score={score:.3f}) -> {preview}")

    prompt = "\n".join(message_lines) + "\nSelection [1-{}]: ".format(max_options)

    while True:
        try:
            answer = input(prompt).strip()
        except (EOFError, OSError) as exc:
            raise AmbiguousRowError(
                f"Ambiguous row at line {line_number}. Provide interactive input to choose a repair."
            ) from exc

        if answer.isdigit():
            choice = int(answer)
            if 1 <= choice <= max_options:
                return candidates[choice - 1][1]

        prompt = f"Invalid selection. Enter a number between 1 and {max_options}: "


def _is_number(value: str) -> bool:
    if value == "":
        return False

    try:
        float(value)
        return True
    except ValueError:
        return False

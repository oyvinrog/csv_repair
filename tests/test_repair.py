import csv
from pathlib import Path

import pytest

import csv_repair

FIXTURES = Path(__file__).parent / "fixtures"


def _rows(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.reader(fh))


def test_repair_preserves_clean_rows(tmp_path: Path) -> None:
    input_file = FIXTURES / "clean.csv"
    output_file = tmp_path / "clean.repaired.csv"

    csv_repair.repair(input_file, output_file)

    assert _rows(output_file) == _rows(input_file)


def test_repair_fixes_description_with_many_commas(tmp_path: Path) -> None:
    input_file = FIXTURES / "corrupt_description.csv"
    expected_file = FIXTURES / "corrupt_description.expected.csv"
    output_file = tmp_path / "description.repaired.csv"

    csv_repair.repair(input_file, output_file)

    assert _rows(output_file) == _rows(expected_file)


def test_repair_supports_custom_description_column(tmp_path: Path) -> None:
    input_file = FIXTURES / "corrupt_notes.csv"
    expected_file = FIXTURES / "corrupt_notes.expected.csv"
    output_file = tmp_path / "notes.repaired.csv"

    csv_repair.repair(input_file, output_file, description_column="NOTES")

    assert _rows(output_file) == _rows(expected_file)


def test_repair_raises_when_description_column_missing(tmp_path: Path) -> None:
    input_file = FIXTURES / "clean.csv"
    output_file = tmp_path / "missing-column.csv"

    with pytest.raises(ValueError, match="Column 'DESCRIPTION_NOT_FOUND' not found"):
        csv_repair.repair(input_file, output_file, description_column="DESCRIPTION_NOT_FOUND")

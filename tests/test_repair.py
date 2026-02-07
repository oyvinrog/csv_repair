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


def test_repair_supports_multiple_text_columns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_file = FIXTURES / "corrupt_multi_text_columns.csv"
    expected_file = FIXTURES / "corrupt_multi_text_columns.expected.csv"
    output_file = tmp_path / "multiple-text-columns.repaired.csv"

    monkeypatch.setattr("builtins.input", lambda _: "1")

    csv_repair.repair(input_file, output_file, description_column=["DESCRIPTION", "NOTES"])

    assert _rows(output_file) == _rows(expected_file)


def test_repair_raises_when_description_column_missing(tmp_path: Path) -> None:
    input_file = FIXTURES / "clean.csv"
    output_file = tmp_path / "missing-column.csv"

    with pytest.raises(ValueError, match="Column 'DESCRIPTION_NOT_FOUND' not found"):
        csv_repair.repair(input_file, output_file, description_column="DESCRIPTION_NOT_FOUND")


def test_repair_asks_user_when_ambiguous_and_uses_selection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_file = FIXTURES / "ambiguous_invoice.csv"
    expected_file = FIXTURES / "ambiguous_invoice.choice1.expected.csv"
    output_file = tmp_path / "ambiguous.repaired.csv"

    monkeypatch.setattr("builtins.input", lambda _: "1")

    csv_repair.repair(input_file, output_file, description_column=["INVOICE", "DESCRIPTION"])

    assert _rows(output_file) == _rows(expected_file)


def test_repair_raises_ambiguous_error_when_user_input_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_file = FIXTURES / "ambiguous_invoice.csv"
    output_file = tmp_path / "ambiguous.noinput.repaired.csv"

    def _raise_eof(_: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", _raise_eof)

    with pytest.raises(csv_repair.AmbiguousRowError, match="Ambiguous row at line 2"):
        csv_repair.repair(input_file, output_file, description_column=["INVOICE", "DESCRIPTION"])


def test_repair_handles_invoice_with_unenclosed_comma_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_file = FIXTURES / "invoice_prefix_corrupt.csv"
    expected_file = FIXTURES / "invoice_prefix_corrupt.expected.csv"
    output_file = tmp_path / "invoice-prefix.repaired.csv"

    monkeypatch.setattr("builtins.input", lambda _: "1")

    csv_repair.repair(input_file, output_file)

    assert _rows(output_file) == _rows(expected_file)

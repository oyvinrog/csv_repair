# csv-repair

`csv-repair` repairs malformed comma-separated files that are missing text qualifiers.

Typical failure case: one column (often `DESCRIPTION`) contains a large free-text value with many commas, but rows are not quoted. This causes rows to have too many columns and break downstream processing.

## Install

```bash
pip install .
```

Install directly from GitHub:

```bash
pip install "git+https://github.com/oyvinrog/csv_repair.git"
```

Using SSH:

```bash
pip install "git+ssh://git@github.com/oyvinrog/csv-repair.git"
```

Pin to a tag or branch:

```bash
pip install "git+https://github.com/oyvinrog/csv_repair.git@v0.1.0"
```

## Usage

```python
import csv_repair

csv_repair.repair("input.csv", "output.csv")
```

Optional argument:

- `description_column` (default: `"DESCRIPTION"`)

```python
csv_repair.repair("input.csv", "output.csv", description_column="NOTES")
```

You can also pass multiple text columns:

```python
csv_repair.repair("input.csv", "output.csv", description_column=["DESCRIPTION", "NOTES"])
```

## Behavior

- Uses the header to determine expected column count.
- Repairs rows with too many columns by merging overflow content into the description column.
- If multiple text columns are provided, scores candidate repairs and picks the most plausible one.
- If two or more candidates are similarly plausible, it prompts you to choose the correct row repair.
- Pads rows with too few columns using empty values.
- Writes valid CSV output using standard CSV quoting rules.
- Preserves row order.

## Development

```bash
pip install -e .[test]
pytest
```

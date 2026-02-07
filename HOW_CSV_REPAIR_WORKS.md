# How `csv_repair` Works

`csv_repair` fixes broken comma-separated files.

It is designed for files where text is **not quoted**, and a text field contains many commas.
That breaks the row into too many columns.

## The Problem

A normal row might look like this:

```csv
ID,CODE,DESCRIPTION,QTY,STATUS
100,A1,Normal description,5,OPEN
```

A broken row (no quotes around long text) might look like this:

```csv
101,B2,This text has,many,commas,inside,7,OPEN
```

Now the row has too many comma splits.

## What `csv_repair` Does

1. Reads the header and counts how many columns should exist.
2. Finds the text column you chose (default is `DESCRIPTION`).
3. For broken rows with too many columns:
   - keeps columns before the text column,
   - keeps columns after the text column from the end of the row,
   - joins the middle pieces back into one text value.
4. For short rows with missing values, fills missing trailing columns with empty values.
5. Writes a valid CSV file with proper quoting.

## Basic Usage

```python
import csv_repair

csv_repair.repair("input.csv", "output.csv")
```

This uses `DESCRIPTION` as the text column.

## Custom Text Column

```python
import csv_repair

csv_repair.repair("input.csv", "output.csv", description_column="NOTES")
```

## Multiple Text Columns

If different rows can break in different text columns, pass a list:

```python
import csv_repair

csv_repair.repair(
    "input.csv",
    "output.csv",
    description_column=["DESCRIPTION", "NOTES"],
)
```

`csv_repair` chooses the most likely text column for each broken row.
If two choices look almost equally good, it asks you to pick one.

## Before and After Example

Before (`input.csv`):

```csv
ID,DESCRIPTION,NOTES,QTY,STATUS
1,Short desc,Brief note,5,OPEN
2,Desc with,many,commas,Stable note,9,OPEN
3,Normal desc,Note has,too,many,commas,11,OPEN
```

After (`output.csv`):

```csv
ID,DESCRIPTION,NOTES,QTY,STATUS
1,Short desc,Brief note,5,OPEN
2,"Desc with,many,commas",Stable note,9,OPEN
3,Normal desc,"Note has,too,many,commas",11,OPEN
```

## Important Notes

- Best for unquoted comma-separated text files.
- Uses the header names, so column names must be correct.
- If a requested text column does not exist, it raises an error.
- In ambiguous rows, it prompts for your choice to avoid silently picking the wrong parse.
- Output is valid CSV and may add quotes where needed.

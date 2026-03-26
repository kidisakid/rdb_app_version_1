# Duplicate Remover Module

**Module:** `src/cleaning/removing_duplicates.py`
**Category:** Cleaning
**Version:** 1.0

---

## Purpose

The Duplicate Remover module identifies and eliminates duplicate rows from your media analytics datasets. When aggregating data from multiple sources — news feeds, social media platforms, press clippings — duplicate entries are inevitable. This module gives you precise control over how duplicates are detected and removed.

---

## When to Use

Use this module when:

- Your dataset contains repeated rows from overlapping data sources
- You need to de-duplicate based on specific columns (e.g., article title + publication date)
- You want to ensure each record in your analysis is unique
- You are merging datasets that may share common entries

---

## What It Does

1. **Full-Row Duplicate Removal** — When no specific columns are selected, the module checks every column to determine if two rows are exact duplicates. Only the first occurrence is kept.

2. **Column-Specific Duplicate Removal** — When you specify particular columns, the module checks only those columns for duplicates. This is useful when two rows may differ in minor fields (e.g., timestamp) but represent the same article or media mention.

3. **Case-Insensitive Column Matching** — Column names you provide are matched case-insensitively against the actual dataset headers, so you don't need to worry about exact casing.

---

## How to Use

### Via the Streamlit App (Recommended)

1. Upload your CSV or Excel file.
2. Check **"Remove Duplicates"** in the pipeline steps.
3. Optionally specify which columns to check for duplicates (leave blank for all columns).
4. Click **"Run Pipeline"**.
5. The result will show only unique rows based on your criteria.

### Via Python (Programmatic)

```python
from src.cleaning.removing_duplicates import remove_duplicates

# Remove exact row duplicates (all columns)
df = remove_duplicates(file_path="data/raw/media_data.csv")

# Remove duplicates based on specific columns
df = remove_duplicates(
    columns=["Article Title", "Source"],
    file_path="data/raw/media_data.csv"
)
```

---

## Input & Output

| Aspect       | Details                                                       |
|-------------|---------------------------------------------------------------|
| **Input**   | A CSV or Excel file, optionally with column names to check    |
| **Output**  | A pandas DataFrame with duplicate rows removed                |
| **Changes** | Rows are removed; columns and remaining data are untouched    |

### Example

**Input (checking duplicates on "Title" and "Source"):**

| Title            | Source       | Date       |
|-----------------|-------------|------------|
| Budget Approved  | Daily News  | 2025-03-01 |
| Budget Approved  | Daily News  | 2025-03-02 |
| New Policy       | The Herald  | 2025-03-01 |

**Output:**

| Title            | Source       | Date       |
|-----------------|-------------|------------|
| Budget Approved  | Daily News  | 2025-03-01 |
| New Policy       | The Herald  | 2025-03-01 |

The second "Budget Approved" row was removed because the Title and Source matched the first row.

---

## Parameters

| Parameter   | Type         | Default             | Description                                         |
|------------|-------------|---------------------|-----------------------------------------------------|
| `columns`   | `list[str]` | `None` (all columns) | Specific columns to check for duplicates            |
| `file_path` | `str`       | Config default path  | Path to the CSV or Excel file                       |

---

## Error Handling

- **Invalid column names**: If you specify columns that don't exist in the dataset, the module raises a `ValueError` with a clear message listing the unrecognized columns.
- **Empty dataset**: If the file has no rows, an empty DataFrame is returned.
- **Case mismatches**: Column names are matched case-insensitively, so `"article title"` will correctly match `"Article Title"`.

---

## Tips for Media Analysts

- **Run Header Normalization first** — Normalizing headers before removing duplicates ensures consistent column names for accurate matching.
- **Choose columns wisely** — For media data, de-duplicating on "Title" + "Source" is often more useful than checking all columns, since timestamps and minor metadata may differ.
- **Check your row count** — Compare the row count before and after to understand how many duplicates were found. The Streamlit app displays this in the preview.
- **Keep first occurrence** — The module always keeps the first occurrence and removes subsequent duplicates.

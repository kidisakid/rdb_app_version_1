# Header Normalization Module

**Module:** `src/cleaning/normalize_headers.py`
**Category:** Cleaning
**Version:** 1.0

---

## Purpose

The Header Normalization module standardizes column names across your uploaded datasets. When working with media analytics data from multiple sources, column names often have inconsistent formatting — extra spaces, mixed casing, or trailing whitespace. This module ensures all headers are clean, consistent, and ready for downstream processing.

---

## When to Use

Use this module when:

- Your dataset has column names with irregular spacing (e.g., `"  Article  Title  "`)
- Column names use inconsistent casing (e.g., `"article title"`, `"ARTICLE TITLE"`, `"Article title"`)
- You want a clean, professional look for your data before exporting or sharing
- You are preparing data for merging with other datasets and need column names to match

---

## What It Does

1. **Trims Excess Whitespace** — Removes leading, trailing, and duplicate internal spaces from every column name. For example, `"  Media   Outlet  "` becomes `"Media Outlet"`.

2. **Converts to Title Case** — Standardizes all column names to Title Case format. For example, `"published date"` becomes `"Published Date"` and `"ARTICLE TITLE"` becomes `"Article Title"`.

---

## How to Use

### Via the Streamlit App (Recommended)

1. Upload your CSV or Excel file using the file uploader.
2. In the pipeline steps, ensure **"Normalize Headers"** is checked.
3. Click **"Run Pipeline"** (or select individual steps).
4. Preview the result — you will see all column names cleaned and title-cased.
5. Download the processed file.

### Via Python (Programmatic)

```python
from src.cleaning.normalize_headers import normalize_headers

# Using default config path
df = normalize_headers()

# Using a specific file
df = normalize_headers(file_path="data/raw/my_media_data.csv")
```

---

## Input & Output

| Aspect       | Details                                                |
|-------------|--------------------------------------------------------|
| **Input**   | A CSV or Excel file with any column naming format      |
| **Output**  | A pandas DataFrame with cleaned, Title Case headers    |
| **Changes** | Only column names are affected; row data is untouched  |

### Example

| Before                  | After                |
|------------------------|----------------------|
| `"  article  title  "` | `"Article Title"`    |
| `"DATE_PUBLISHED"`     | `"Date_Published"`   |
| `"media outlet"`       | `"Media Outlet"`     |
| `"   AUTHOR   NAME  "` | `"Author Name"`     |

---

## Parameters

| Parameter   | Type   | Default              | Description                        |
|------------|--------|----------------------|------------------------------------|
| `file_path` | `str`  | Config default path  | Path to the CSV or Excel file      |

---

## Error Handling

- If the file path is invalid or the file cannot be read, the CSV handler will attempt multiple encodings and delimiters before raising an error.
- If the file is empty, an empty DataFrame is returned with normalized headers.

---

## Tips for Media Analysts

- **Always run this step first** — It ensures all subsequent modules (duplicate removal, date metadata, translation) can reference columns by their standardized names.
- **Check your column names after processing** — The preview table in the Streamlit app shows the updated headers immediately.
- **Title Case preserves underscores** — If your original headers use underscores (e.g., `date_published`), they will become `Date_Published`. This is expected behavior.

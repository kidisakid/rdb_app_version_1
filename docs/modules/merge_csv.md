# CSV Merge Module

**Module:** `src/merge/merge_csv.py`
**Category:** Merge
**Version:** 2.0

---

## Purpose

The CSV Merge module combines multiple CSV or Excel files into a single consolidated dataset. Instead of relying on filename prefixes for grouping, it lets you select a common column shared across all uploaded files. The merge concatenates all rows and sorts the result by the chosen column, giving you an organized, unified dataset ready for downstream analysis.

---

## When to Use

Use this module when:

- You have separate media coverage files from different sources, countries, or time periods that need to be combined
- You need to consolidate multiple data exports into one unified dataset for cross-cutting analysis
- Your files share at least one common column (e.g., `Date`, `Country`, `Source`) that should serve as the organizing key

---

## What It Does

1. **Accepts Multiple Files** — Takes a list of uploaded CSV or Excel files (via Streamlit multi-file upload).

2. **Detects Common Columns** — Reads the column headers from every uploaded file and computes the intersection — columns that exist in ALL files.

3. **Presents Column Selection** — Shows a dropdown of common columns so you can choose which one to merge on.

4. **Reads with Smart Encoding Detection** — Each file is read using multi-encoding, multi-delimiter fallback logic (UTF-16, UTF-8, UTF-8-SIG, Latin-1, CP-1252; tab, comma, semicolon delimiters). UTF-16 files with BOM are automatically detected and prioritized.

5. **Filters Null Rows** — Rows where the selected merge column has a null/empty value are dropped from each file before merging.

6. **Concatenates All Files** — All successfully read DataFrames are stacked vertically (`pd.concat`), preserving all columns even if files have different schemas.

7. **Sorts by Merge Column** — The final merged DataFrame is sorted by the selected column for organized output.

---

## How to Use

### Via the Streamlit App (Recommended)

1. Click **"Merge Data"** in the sidebar to open the merge tool.
2. Upload **two or more** CSV or Excel files using the file uploader.
3. Review the **File Summary** table showing row and column counts for each file.
4. In the **Merge Column** dropdown, select the column you want to merge on (only columns common to ALL files are shown).
5. Click **"Merge Files"**.
6. Preview the merged result and download it as CSV or Excel.

### Via Python (Programmatic)

```python
from src.merge.merge_csv import merge_csv, get_common_columns

# Find common columns across files
common_cols = get_common_columns(uploaded_file_list)

# Merge using a selected common column
df = merge_csv(uploaded_files=uploaded_file_list, merge_column="Date")

# Single file mode (returns as-is)
df = merge_csv(file_path="data/raw/single_file.csv")
```

---

## Input & Output

| Aspect       | Details                                                                  |
|-------------|--------------------------------------------------------------------------|
| **Input**   | Two or more CSV/Excel files uploaded via Streamlit                       |
| **Output**  | A single pandas DataFrame with all rows merged, sorted by chosen column  |
| **Changes** | Null rows in merge column dropped; result sorted by merge column         |

### Example

**Input Files:**

`ID_news_coverage.csv`:
| Date        | Headline           | Source      | Country   |
|-------------|-------------------|-------------|-----------|
| 01-Jan-2026 | New Policy         | Daily News  | Indonesia |
| 02-Jan-2026 | Market Update      | Tribune     | Indonesia |

`MY_news_coverage.csv`:
| Date        | Headline           | Source      | Country   |
|-------------|-------------------|-------------|-----------|
| 01-Jan-2026 | Trade Deal         | Star News   | Malaysia  |
| 03-Jan-2026 | Budget Approved    | Malay Mail  | Malaysia  |

**Merged Output (merge column: `Date`):**

| Date        | Headline           | Source      | Country   |
|-------------|-------------------|-------------|-----------|
| 01-Jan-2026 | New Policy         | Daily News  | Indonesia |
| 01-Jan-2026 | Trade Deal         | Star News   | Malaysia  |
| 02-Jan-2026 | Market Update      | Tribune     | Indonesia |
| 03-Jan-2026 | Budget Approved    | Malay Mail  | Malaysia  |

---

## Parameters

| Parameter        | Type                    | Default           | Description                                              |
|-----------------|------------------------|--------------------|----------------------------------------------------------|
| `file_path`      | `str`                  | Config default     | Path for single-file mode                                |
| `uploaded_files`  | `list[UploadedFile]`  | `None`             | List of Streamlit uploaded file objects                   |
| `merge_column`   | `str`                  | `None`             | Common column name to filter nulls and sort the result by |

---

## Error Handling

- **No common columns**: If the uploaded files share no column names, an error message is displayed and merging is blocked.
- **No valid files**: If none of the uploaded files can be read, an empty DataFrame is returned.
- **Mixed schemas**: Files with different columns are merged safely — missing columns are filled with `NaN`.
- **Encoding issues**: The module tries multiple encodings and delimiters per file, with automatic UTF-16 BOM detection.
- **Minimum file requirement**: The Streamlit UI only enables merging when 2 or more files are uploaded.

---

## Tips for Media Analysts

- **Choose a meaningful merge column** — Pick a column like `Date`, `Country`, or `Source` that is consistent across all your files. This determines how the merged output is organized.
- **Run merge first** — If you're combining files, run the merge step before cleaning and transformation so all subsequent steps operate on the full combined dataset.
- **Check column alignment** — If files from different sources have slightly different column names, the common column dropdown may be empty. Ensure column headers match exactly across files (run Header Normalization on individual files first if needed).
- **UTF-16 files are supported** — Files exported from tools like Meltwater or Cision in UTF-16 tab-delimited format are automatically detected and read correctly.

# CSV Merge Module

**Module:** `src/merge/merge_csv.py`
**Category:** Merge
**Version:** 1.0

---

## Purpose

The CSV Merge module combines multiple CSV files into a single consolidated dataset. It is designed for media analytics workflows where coverage data arrives as separate files per country or region. Each file is tagged with a Country Code derived from its filename, so the merged result retains traceability back to its source.

---

## When to Use

Use this module when:

- You have separate media coverage files for different countries (e.g., `PH_coverage.csv`, `US_coverage.csv`)
- You need to consolidate multiple data exports into one unified dataset for cross-country analysis
- You want an automatic identifier column showing which file each row came from

---

## What It Does

1. **Accepts Multiple Files** — Takes a list of uploaded CSV files (via Streamlit multi-file upload).

2. **Extracts Country Code** — Reads the first two characters of each filename, converts them to uppercase, and uses this as the Country Code (e.g., `ph_media_data.csv` becomes `PH`).

3. **Reads with Smart Encoding Detection** — Each file is read using the same multi-encoding, multi-delimiter fallback logic as the CSV Handler (UTF-8, UTF-8-SIG, UTF-16, Latin-1, CP-1252; tab, comma, semicolon delimiters).

4. **Adds Country_Code Column** — A new `Country_Code` column is prepended to each file's data before merging.

5. **Concatenates All Files** — All successfully read DataFrames are stacked vertically (`pd.concat`), preserving all columns even if files have different schemas.

---

## How to Use

### Via the Streamlit App (Recommended)

1. Upload **two or more** CSV or Excel files using the file uploader.
2. Check **"Merge CSV files"** in the pipeline steps (this option only appears when 2+ files are uploaded).
3. Click **"Run Pipeline"**.
4. The merged result will include a `Country_Code` column identifying each row's source file.
5. Download the consolidated dataset.

### Via Python (Programmatic)

```python
from src.merge.merge_csv import merge_csv

# With Streamlit uploaded files
df = merge_csv(uploaded_files=uploaded_file_list)

# Single file mode (returns as-is)
df = merge_csv(file_path="data/raw/single_file.csv")
```

---

## Input & Output

| Aspect       | Details                                                            |
|-------------|---------------------------------------------------------------------|
| **Input**   | Two or more CSV/Excel files uploaded via Streamlit                  |
| **Output**  | A single pandas DataFrame with all rows merged + Country_Code column |
| **Changes** | New `Country_Code` column added; all source rows combined           |

### Example

**Input Files:**

`PH_coverage.csv`:
| Title              | Source      |
|-------------------|-------------|
| New Policy         | Daily News  |

`US_coverage.csv`:
| Title              | Source      |
|-------------------|-------------|
| Budget Approved    | NY Times    |

**Merged Output:**

| Country_Code | Title              | Source      |
|-------------|-------------------|-------------|
| PH           | New Policy         | Daily News  |
| US           | Budget Approved    | NY Times    |

---

## Parameters

| Parameter        | Type                    | Default           | Description                                    |
|-----------------|------------------------|--------------------|------------------------------------------------|
| `file_path`      | `str`                  | Config default     | Path for single-file mode                      |
| `uploaded_files`  | `list[UploadedFile]`  | `None`             | List of Streamlit uploaded file objects         |

---

## File Naming Convention

The Country Code is extracted from the **first two characters** of the filename:

| Filename                  | Country Code |
|--------------------------|-------------|
| `PH_media_coverage.csv`  | `PH`        |
| `us_news_data.csv`       | `US`        |
| `fr-articles-2025.csv`   | `FR`        |
| `data_export.csv`        | `DA`        |

**Important:** Name your files with the country code as the first two characters for accurate tagging.

---

## Error Handling

- **No valid files**: If none of the uploaded files can be read, an empty DataFrame is returned.
- **Mixed schemas**: Files with different columns are merged safely — missing columns are filled with `NaN`.
- **Encoding issues**: The module tries multiple encodings and delimiters per file, just like the CSV Handler.
- **Minimum file requirement**: The Streamlit UI only enables this step when 2 or more files are uploaded.

---

## Tips for Media Analysts

- **Name files consistently** — Use ISO 3166-1 alpha-2 country codes as the filename prefix (e.g., `PH_`, `US_`, `JP_`) for accurate Country Code extraction.
- **Run merge first** — If you're combining files, run the merge step before cleaning and transformation so all subsequent steps operate on the full combined dataset.
- **Check column alignment** — If files from different countries have different column names, the merge will include all columns but some cells may be empty. Run Header Normalization after merging to catch inconsistencies.

# CSV Handler Utility

**Module:** `src/utils/csv_handler.py`
**Category:** Utility
**Version:** 1.0

---

## Purpose

The CSV Handler is the foundational utility module that powers all file reading and writing across the application. It provides robust, fault-tolerant CSV and Excel I/O operations, automatically handling the encoding and delimiter inconsistencies that are common in real-world media data exports.

---

## When It Is Used

This module is called automatically by every other module in the pipeline. You typically do not need to interact with it directly, but understanding its behavior helps troubleshoot file loading issues.

It is used when:

- Any module reads your uploaded CSV or Excel file
- Processed data is saved back to a temporary file between pipeline steps
- The final result is prepared for download

---

## What It Does

### `read_csv(file_path)`

Reads a CSV or Excel file into a pandas DataFrame with intelligent fallback:

1. **Tries multiple encodings** — Attempts `utf-8`, `utf-8-sig`, `latin1`, and `cp1252` in order.
2. **Tries multiple delimiters** — For each encoding, tries tab (`\t`), comma (`,`), and semicolon (`;`).
3. **Falls back to Excel** — If all CSV attempts fail, tries reading the file as an Excel workbook (`.xlsx` / `.xls`).
4. **Returns the first successful read** — Stops as soon as data loads correctly.

### `write_csv(data, file_path)`

Writes a pandas DataFrame to a CSV file using UTF-8 encoding, without the index column.

### `append_csv(data, file_path)`

Appends rows to an existing CSV file without writing a header row. Useful for incremental data collection.

### `read_csv_to_dict(file_path)`

Reads a CSV file and returns the data as a list of Python dictionaries (one dict per row), which is used internally by the date metadata module.

---

## Supported Formats

| Format          | Extensions         | Support Level          |
|----------------|-------------------|------------------------|
| CSV (UTF-8)     | `.csv`            | Full (primary)         |
| CSV (Latin-1)   | `.csv`            | Full (fallback)        |
| CSV (CP-1252)   | `.csv`            | Full (fallback)        |
| Tab-separated   | `.csv`, `.tsv`    | Full (auto-detected)   |
| Semicolon-separated | `.csv`        | Full (auto-detected)   |
| Excel           | `.xlsx`, `.xls`   | Full (final fallback)  |

---

## Error Handling

- **File not found**: Raises a standard Python `FileNotFoundError`.
- **Unreadable file**: If all encoding/delimiter/Excel combinations fail, raises an exception with details about what was attempted.
- **Corrupted data**: Partially readable files may load with warnings; check your DataFrame shape after loading.

---

## Tips for Media Analysts

- **You don't need to worry about file encoding** — The handler tries the four most common encodings automatically. Files exported from Excel, Google Sheets, or media monitoring platforms should all work.
- **Semicolons and tabs are fine** — Some European tools export CSVs with semicolons instead of commas. The handler detects this automatically.
- **Excel files work too** — If your media data is in `.xlsx` format, you can upload it directly without converting to CSV first.
- **If a file won't load** — Check that the file is not password-protected, corrupted, or in an unsupported format (e.g., `.ods`, `.json`).

# Date Metadata Extraction Module

**Module:** `src/transformation/add_dates_metadata.py`
**Category:** Transformation
**Version:** 1.0

---

## Purpose

The Date Metadata Extraction module automatically detects date columns in your media dataset and generates derived time-based columns — Year, Month, Day, and Quarter. These enriched fields are essential for time-series analysis, trend tracking, seasonal reporting, and filtering media coverage by specific time periods.

---

## When to Use

Use this module when:

- You need to analyze media coverage trends over time (monthly, quarterly, yearly)
- Your dataset has a date column but lacks broken-out time components
- You want to filter or group articles by quarter for executive reports
- You are preparing data for visualizations that require separate Year/Month/Day fields

---

## What It Does

1. **Auto-Detects the Date Column** — Scans your dataset for common date column names in this priority order:
   - `"date"`, `"date_published"`, `"published_date"`, `"published"`, `"datetime"`, `"timestamp"`
   - Falls back to any column containing the word `"date"`

2. **Parses Dates Intelligently** — Converts the detected column to proper datetime format, supporting international date formats (day-first parsing enabled).

3. **Generates Four New Columns** — Inserted immediately after the detected date column:

   | New Column   | Format           | Example         |
   |-------------|------------------|-----------------|
   | **Year**     | Integer          | `2025`          |
   | **Month**    | Abbreviated name | `"Mar"`         |
   | **Day**      | Integer          | `15`            |
   | **Quarter**  | Integer (1-4)    | `1`             |

---

## How to Use

### Via the Streamlit App (Recommended)

1. Upload your CSV or Excel file containing a date column.
2. Check **"Add Date Metadata"** in the pipeline steps.
3. Click **"Run Pipeline"**.
4. The result will show four new columns added after your date column.
5. Download the enriched dataset.

### Via Python (Programmatic)

```python
from src.transformation.add_dates_metadata import add_dates_metadata

# Using default config path
df = add_dates_metadata()

# Using a specific file
df = add_dates_metadata(file_path="data/raw/media_coverage.csv")
```

---

## Input & Output

| Aspect       | Details                                                                  |
|-------------|--------------------------------------------------------------------------|
| **Input**   | A CSV or Excel file with at least one recognizable date column           |
| **Output**  | A pandas DataFrame with Year, Month, Day, and Quarter columns added      |
| **Changes** | Four new columns inserted after the date column; existing data untouched |

### Example

**Input:**

| Title            | Date Published | Source      |
|-----------------|----------------|-------------|
| New Policy       | 15/03/2025     | Daily News  |
| Budget Update    | 22/06/2025     | The Herald  |
| Election Results | 05/11/2025     | Tribune     |

**Output:**

| Title            | Date Published | Year | Month | Day | Quarter | Source      |
|-----------------|----------------|------|-------|-----|---------|-------------|
| New Policy       | 15/03/2025     | 2025 | Mar   | 15  | 1       | Daily News  |
| Budget Update    | 22/06/2025     | 2025 | Jun   | 22  | 2       | The Herald  |
| Election Results | 05/11/2025     | 2025 | Nov   | 5   | 4       | Tribune     |

---

## Parameters

| Parameter   | Type   | Default             | Description                   |
|------------|--------|---------------------|-------------------------------|
| `file_path` | `str`  | Config default path  | Path to the CSV or Excel file |

---

## Supported Date Column Names

The module searches for date columns in this exact priority order:

1. `date`
2. `date_published`
3. `published_date`
4. `published`
5. `datetime`
6. `timestamp`
7. Any column whose name contains `"date"` (case-insensitive)

---

## Error Handling

- **No date column found**: Raises a `ValueError` with the message: *"No date column found in the dataset."* Ensure your date column uses one of the recognized names listed above.
- **Unparseable dates**: Rows with invalid date values will result in `NaT` (Not a Time) and the derived columns will be `NaN` for those rows.
- **Multiple date columns**: The module uses the first match from the priority list. If you have multiple date columns, rename the desired one to `"date"` to ensure it is selected.

---

## Tips for Media Analysts

- **Run Header Normalization first** — Clean headers help the auto-detection find your date column reliably.
- **Check date formats** — The module supports international formats (DD/MM/YYYY) by default. If your dates are in US format (MM/DD/YYYY), results may be incorrect for ambiguous dates like `03/04/2025`. Verify a few rows after processing.
- **Use Quarter for executive summaries** — The Quarter column (1-4) maps directly to fiscal quarters, making it ideal for quarterly media coverage reports.
- **Month abbreviations** — Months are stored as three-letter abbreviations (Jan, Feb, Mar, etc.) for readability in reports and charts.

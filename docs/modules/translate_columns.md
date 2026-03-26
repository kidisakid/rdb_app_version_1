# Column Translation Module

**Module:** `src/transformation/translate_columns.py`
**Category:** Transformation
**Version:** 1.0

---

## Purpose

The Column Translation module translates text content in selected columns from one language to another using Google Translate. It is designed for media analytics workflows where coverage data arrives in multiple languages and needs to be unified into a single language (typically English) for consistent analysis, sentiment scoring, and reporting.

---

## When to Use

Use this module when:

- Your media dataset contains articles, headlines, or summaries in foreign languages
- You need all text in a common language for keyword analysis or sentiment scoring
- You are consolidating international media coverage into a single report
- You want to understand the content of non-English media mentions

---

## What It Does

1. **Translates Selected Columns** — You choose which text columns to translate (e.g., "Title", "Summary"). The module creates new columns prefixed with `"T_"` containing the translated text, preserving the originals.

2. **Auto-Detects Source Language** — By default, the module detects the language of each cell automatically. You can also specify a fixed source language if your data is uniform.

3. **Smart Optimization** — The module employs several strategies to minimize API calls and speed up processing:

   - **Similarity Grouping**: Uses TF-IDF vectorization and cosine similarity (threshold: 0.85) to group nearly identical texts. Only the representative text from each group is translated, and the result is applied to all group members.
   - **Translation Caching**: Previously translated text is cached so identical strings are never translated twice.
   - **Language Skip**: Text already in the target language is detected and skipped automatically.

4. **Parallel Processing** — Uses multi-threaded execution to translate multiple texts concurrently, significantly speeding up large datasets.

5. **Progress Tracking** — A progress bar shows real-time translation progress in both the CLI and Streamlit interfaces.

---

## How to Use

### Via the Streamlit App (Recommended)

1. Upload your CSV or Excel file.
2. Check **"Translate Columns"** in the pipeline steps.
3. Select the target language (default: English).
4. Choose which columns to translate.
5. Click **"Run Pipeline"**.
6. New columns prefixed with `"T_"` will appear with translated content.
7. Download the result.

### Via Python (Programmatic)

```python
from src.transformation.translate_columns import translate_columns

# Translate all text columns to English
df = translate_columns(
    target_language='en',
    file_path="data/raw/international_media.csv"
)

# Translate specific columns from Spanish to English
df = translate_columns(
    target_language='en',
    source_language='es',
    columns_to_process=["Titulo", "Resumen"],
    file_path="data/raw/spanish_coverage.csv"
)
```

---

## Input & Output

| Aspect       | Details                                                                |
|-------------|------------------------------------------------------------------------|
| **Input**   | A CSV or Excel file with text columns in any language                  |
| **Output**  | A pandas DataFrame with new `T_` prefixed columns containing translations |
| **Changes** | New columns added; original columns preserved                          |

### Example

**Input:**

| Title                      | Source         |
|---------------------------|----------------|
| Nouveau budget approuve    | Le Monde       |
| Presupuesto actualizado    | El Pais        |
| New policy announced       | Daily News     |

**Output (target: English):**

| Title                      | T_Title                    | Source         |
|---------------------------|---------------------------|----------------|
| Nouveau budget approuve    | New budget approved        | Le Monde       |
| Presupuesto actualizado    | Updated budget             | El Pais        |
| New policy announced       | New policy announced       | Daily News     |

Note: The third row was already in English, so it was detected and skipped (the original text is copied as-is).

---

## Parameters

| Parameter            | Type           | Default   | Description                                     |
|---------------------|---------------|-----------|--------------------------------------------------|
| `target_language`    | `str`         | `'en'`    | Target language code (e.g., `'en'`, `'fr'`, `'es'`) |
| `source_language`    | `str`         | `'auto'`  | Source language code, or `'auto'` for detection   |
| `columns_to_process` | `list[str]`  | `None`    | Specific columns to translate (None = all text)   |
| `file_path`          | `str`         | Config default | Path to the CSV or Excel file                |
| `progress_callback`  | `callable`   | `None`    | Callback function for progress updates            |

### Common Language Codes

| Language   | Code |
|-----------|------|
| English    | `en` |
| Spanish    | `es` |
| French     | `fr` |
| German     | `de` |
| Filipino   | `tl` |
| Japanese   | `ja` |
| Korean     | `ko` |
| Chinese    | `zh` |
| Arabic     | `ar` |
| Portuguese | `pt` |

---

## Performance Optimizations

The translation module is the most computationally intensive step in the pipeline. Here's how it stays efficient:

| Optimization          | How It Works                                                       | Benefit                          |
|----------------------|-------------------------------------------------------------------|----------------------------------|
| **Similarity Groups** | Groups texts with 85%+ similarity using TF-IDF vectors           | Reduces API calls by 20-60%      |
| **Caching**          | Stores translations in memory for the session                     | Eliminates redundant calls       |
| **Language Skip**    | Detects text already in target language                           | Avoids unnecessary translations  |
| **Parallel Threads** | Translates multiple texts simultaneously (up to 10 threads)       | Speeds up large datasets         |

---

## Error Handling

- **Translation API failures**: If a single translation fails, the cell is filled with `"NA"` and processing continues. The overall pipeline is not interrupted.
- **Empty cells**: Empty or null values are skipped.
- **Rate limiting**: The parallel thread pool is capped at 10 workers to avoid overwhelming the translation API.
- **Invalid language codes**: The Google Translate API will return an error if an unsupported language code is used. Refer to the language codes table above.

---

## Tips for Media Analysts

- **Be patient with large datasets** — Translation is the slowest step because it makes external API calls. A dataset with 1,000 rows and 2 text columns may take several minutes.
- **Translate only what you need** — Select specific columns rather than translating everything. Translating a "Source" or "URL" column is wasteful.
- **Check the T_ columns** — Machine translation is not perfect. Spot-check a few translations, especially for industry-specific terminology.
- **Run this step last** — Translation should follow header normalization, duplicate removal, and date metadata extraction. This ensures you're not translating duplicate or irrelevant data.
- **Internet connection required** — This module requires an active internet connection to reach the Google Translate API.

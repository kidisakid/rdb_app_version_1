from typing import List, Dict, Set, Tuple, Optional, Callable
import pandas as pd
import numpy as np
import config
from csv_handler import read_csv_to_dict
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import os
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def translate_columns(
    target_language: str = 'en',
    source_language: str = 'auto',
    columns_to_process: Optional[List[str]] = None,
    file_path: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> pd.DataFrame:
    """
    Translate text columns in the dataset.
    Allows user to select which columns to translate from all available columns.
    Creates new columns with "T_" prefix for each translated column.

    Args:
        target_language: Target language code (default: 'en' for English)
        source_language: Source language code (default: 'auto' for auto-detect)
        file_path: Path to CSV file. If None, uses config.RAW_DATA_FILE (for CLI/script).

    Returns:
        DataFrame with translated columns (prefixed with "T_")

    Raises:
        ValueError: If the dataset is empty or no columns are selected
    """
    try:
        path = file_path if file_path is not None else str(config.RAW_DATA_FILE)
        data_list: List[Dict] = read_csv_to_dict(path)
    except Exception as e:
        raise RuntimeError(f"Failed to read file for translation: {e}") from e

    if not data_list:
        raise ValueError("The dataset is empty")

    first_row = data_list[0]
    all_columns = list(first_row.keys())

    if not all_columns:
        raise ValueError("No columns found in the dataset")

    # Use provided columns or default to all columns
    if columns_to_process is None:
        columns_to_process = all_columns
    else:
        valid_cols = [c for c in columns_to_process if c in all_columns]
        if not valid_cols and columns_to_process:
            raise ValueError(f"None of the selected columns exist. Available: {all_columns}")
        columns_to_process = valid_cols if valid_cols else all_columns

    if not columns_to_process:
        raise ValueError("No columns selected for translation")

    df = pd.DataFrame(data_list)
    df_translated = df.copy()

    # Get number of workers (default to CPU count, but cap at reasonable number for API calls)
    num_workers = min(os.cpu_count() or 4, 10)

    # Translate each selected column
    total_cols = len(columns_to_process)
    total_rows_global = len(df_translated)
    total_work = total_cols * total_rows_global
    for col_idx, col_name in enumerate(columns_to_process):
        if col_name not in df_translated.columns:
            continue
        if progress_callback:
            progress_callback(
                col_idx * total_rows_global, total_work,
                f"Translating: {col_idx * total_rows_global}/{total_work} rows"
            )

        translated_col_name = f"T_{col_name}"

        # Get column series for vectorized operations
        col_series = df_translated[col_name]
        total_rows = len(col_series)

        # Thread-safe translation cache to avoid re-translating duplicate texts
        translation_cache: Dict[str, str] = {}
        translation_cache_lock = Lock()
        # Cache for language detection results
        lang_cache: Dict[str, str] = {}
        lang_cache_lock = Lock()

        # Pre-process: identify empty/null values
        is_empty = col_series.isna() | (col_series.astype(str).str.strip() == '')

        # Prepare data: collect all non-empty texts with their indices
        items_to_translate = []
        text_to_indices: Dict[str, List[int]] = {}

        for idx, value in enumerate(col_series):
            if not is_empty.iloc[idx]:
                str_value = str(value).strip()
                items_to_translate.append((idx, str_value))
                if str_value not in text_to_indices:
                    text_to_indices[str_value] = []
                text_to_indices[str_value].append(idx)

        if not items_to_translate:
            # All values are empty
            df_translated[translated_col_name] = [''] * total_rows
            if progress_callback:
                done = (col_idx + 1) * total_rows_global
                progress_callback(done, total_work, f"Translating: {done}/{total_work} rows")
            continue

        # Step 1: Vectorize all unique texts
        unique_texts = list(text_to_indices.keys())
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words=None,
            ngram_range=(1, 2),
            max_features=5000,
            min_df=1,
            max_df=0.95
        )

        try:
            vectors = vectorizer.fit_transform(unique_texts)

            # Step 2: Compute similarity matrix
            similarity_matrix = cosine_similarity(vectors)

            # Step 3: Group similar texts (similarity threshold: 0.85)
            similarity_threshold = 0.85
            groups: List[List[str]] = []
            used_texts: Set[str] = set()

            for i, text in enumerate(unique_texts):
                if text in used_texts:
                    continue

                similar_indices = np.where(similarity_matrix[i] >= similarity_threshold)[0]
                similar_texts = [unique_texts[j] for j in similar_indices]

                groups.append(similar_texts)
                used_texts.update(similar_texts)

        except Exception:
            # Fallback: if vectorization fails, use original method
            groups = [[text] for text in unique_texts]

        # Step 4: Translate groups (translate one representative, apply to all similar)
        def translate_group(group: List[str]) -> Tuple[Dict[str, str], str]:
            """Translate a group of similar texts. Returns (translations_dict, status)"""
            translations = {}

            # Use the first (shortest) text as representative for translation
            representative = min(group, key=len)

            try:
                str_value = representative.strip()

                # Check cache first
                with translation_cache_lock:
                    if str_value in translation_cache:
                        cached_translation = translation_cache[str_value]
                        for text in group:
                            translations[text] = cached_translation
                        return translations, 'cached'

                # Language detection only for strings longer than 3 characters
                if len(str_value) > 3:
                    with lang_cache_lock:
                        if str_value in lang_cache:
                            detected_lang = lang_cache[str_value]
                        else:
                            try:
                                detected_lang = detect(str_value)
                                lang_cache[str_value] = detected_lang
                            except (LangDetectException, Exception):
                                detected_lang = None

                    if detected_lang == target_language:
                        with translation_cache_lock:
                            translation_cache[str_value] = str_value
                        for text in group:
                            translations[text] = str_value
                        return translations, 'skipped'

                # Translate the representative text
                translator = GoogleTranslator(source=source_language, target=target_language)
                translated_text = translator.translate(str_value)

                # Cache and apply to all similar texts in group
                with translation_cache_lock:
                    for text in group:
                        translation_cache[text] = translated_text
                        translations[text] = translated_text

                return translations, 'translated'

            except Exception:
                # On error, return 'NA' for all texts in group
                for text in group:
                    translations[text] = 'NA'
                return translations, 'error'

        # Translate all groups in parallel
        translated_values = [''] * total_rows
        skipped_count = 0
        cached_count = 0
        grouped_count = 0
        completed = 0
        num_groups = len(groups)
        rows_filled = 0

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            future_to_group = {executor.submit(translate_group, group): group for group in groups}

            with tqdm(
                total=num_groups, desc=f"Translating {col_name}",
                unit="group", disable=progress_callback is not None
            ) as pbar:
                for future in as_completed(future_to_group):
                    try:
                        group_translations, status = future.result()
                        group = future_to_group[future]

                        for text, translation in group_translations.items():
                            if text in text_to_indices:
                                for idx in text_to_indices[text]:
                                    translated_values[idx] = translation
                        rows_filled += sum(
                            len(text_to_indices.get(text, [])) for text in group_translations
                        )
                        if progress_callback:
                            current_work = col_idx * total_rows_global + rows_filled
                            progress_callback(
                                current_work, total_work,
                                f"Translating: {current_work}/{total_work} rows"
                            )

                        if len(group) > 1:
                            grouped_count += len(group) - 1

                        if status == 'cached':
                            cached_count += len(group)
                        elif status == 'skipped':
                            skipped_count += len(group)

                        completed += 1
                        pbar.set_postfix({
                            'groups': num_groups,
                            'grouped': grouped_count,
                            'cached': cached_count,
                            'skipped': skipped_count
                        })
                        pbar.update(1)
                    except Exception:
                        group = future_to_group[future]
                        for text in group:
                            if text in text_to_indices:
                                for idx in text_to_indices[text]:
                                    translated_values[idx] = 'NA'
                        rows_filled += sum(
                            len(text_to_indices.get(text, [])) for text in group
                        )
                        if progress_callback:
                            current_work = col_idx * total_rows_global + rows_filled
                            progress_callback(
                                current_work, total_work,
                                f"Translating: {current_work}/{total_work} rows"
                            )
                        completed += 1
                        pbar.update(1)

        df_translated[translated_col_name] = translated_values

    try:
        if progress_callback and total_work:
            progress_callback(total_work, total_work, f"Translating: {total_work}/{total_work} rows - done")
    except Exception:
        pass
    return df_translated

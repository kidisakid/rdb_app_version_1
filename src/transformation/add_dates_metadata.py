from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
import config
from csv_handler import read_csv_to_dict


def add_dates_metadata(file_path: Optional[str | Path] = None) -> pd.DataFrame:
    """
    Add date metadata columns to the dataset based on the Date column.
    Reads the raw data file as a list, finds the Date column (case-insensitive),
    and adds derived columns.

    Args:
        file_path: Path to CSV file. If None, uses config.RAW_DATA_FILE (for CLI/script).

    Returns:
        DataFrame with date metadata columns added

    Raises:
        ValueError: If the Date column is not found in the dataset
    """
    path = str(file_path) if file_path is not None else str(config.RAW_DATA_FILE)
    data_list: List[Dict] = read_csv_to_dict(path)

    if not data_list:
        raise ValueError("The dataset is empty")

    first_row = data_list[0]
    all_cols = list(first_row.keys())
    col_lower = {c.lower(): c for c in all_cols}
    # Prefer exact "date", then common date-like names, then any column containing "date"
    date_candidates = [
        "date",
        "date_published",
        "published_date",
        "published",
        "datetime",
        "timestamp",
    ]
    date_column = None
    for candidate in date_candidates:
        if candidate in col_lower:
            date_column = col_lower[candidate]
            break
    if date_column is None:
        for col in all_cols:
            if "date" in col.lower():
                date_column = col
                break
    if date_column is None:
        available_columns = list(first_row.keys())
        raise ValueError(
            f"Date column not found in the dataset. "
            f"Available columns: {available_columns}"
        )

    df = pd.DataFrame(data_list)

    df_with_metadata = df.copy()

    if date_column not in df_with_metadata.columns:
        available_columns = list(df_with_metadata.columns)
        raise ValueError(
            f"Date column '{date_column}' not found in the DataFrame. "
            f"Available columns: {available_columns}"
        )

    try:
        df_with_metadata[date_column] = pd.to_datetime(
            df_with_metadata[date_column], errors='coerce', dayfirst=True
        )

        df_with_metadata['Year'] = df_with_metadata[date_column].dt.year.astype('Int64')
        df_with_metadata['Month'] = df_with_metadata[date_column].dt.strftime('%b')
        df_with_metadata['Day'] = df_with_metadata[date_column].dt.day.astype('Int64')
        df_with_metadata['Quarter'] = df_with_metadata[date_column].dt.quarter.astype('Int64')

        columns = list(df_with_metadata.columns)
        date_index = columns.index(date_column)

        metadata_cols = ['Year', 'Month', 'Day', 'Quarter']
        for col in metadata_cols:
            if col in columns:
                columns.remove(col)

        for i, col in enumerate(metadata_cols, 1):
            columns.insert(date_index + i, col)

        df_with_metadata = df_with_metadata[columns]

    except Exception as e:
        raise ValueError(
            f"Error processing Date column '{date_column}': {str(e)}"
        )

    return df_with_metadata

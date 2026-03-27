from pathlib import Path
from typing import Optional, List, Tuple
import pandas as pd
import config
from csv_handler import read_csv


def remove_duplicates(
    columns: Optional[List[str]] = None,
    file_path: Optional[str | Path] = None,
) -> pd.DataFrame:
    """
    Remove duplicates from the dataset.

    Args:
        columns: List of column names to check for duplicates, or None to check all columns.
                If None and running interactively, will prompt user for input.
                Column names are matched case-insensitively.
        file_path: Path to CSV file. If None, uses config.RAW_DATA_FILE (for CLI/script).

    Returns:
        DataFrame with duplicates removed
    """
    path = str(file_path) if file_path is not None else str(config.RAW_DATA_FILE)
    df = read_csv(path)
    df_work = df.copy()
    column_map = {col.lower(): col for col in df_work.columns}

    def match_columns(user_columns: List[str]) -> Tuple[List[str], List[str]]:
        """Match user input columns to actual column names (case-insensitive)."""
        matched_columns: List[str] = []
        invalid_columns: List[str] = []

        for user_col in user_columns:
            user_col_lower = user_col.strip().lower()
            if user_col_lower in column_map:
                matched_columns.append(column_map[user_col_lower])
            else:
                invalid_columns.append(user_col)

        return matched_columns, invalid_columns

    if columns is None:
        df_clean = df_work.drop_duplicates()
    else:
        user_columns = [col.strip() if isinstance(col, str) else col for col in columns]
        columns_to_check, invalid_columns = match_columns(user_columns)

        if invalid_columns:
            raise ValueError(f"Invalid columns: {invalid_columns}")

        if not columns_to_check:
            df_clean = df_work.drop_duplicates()
        else:
            df_clean = df_work.drop_duplicates(subset=columns_to_check)

    return df_clean

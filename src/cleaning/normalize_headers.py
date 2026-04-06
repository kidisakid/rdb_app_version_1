from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import config
from csv_handler import read_csv


def normalize_headers(file_path: Optional[str | Path] = None) -> pd.DataFrame:
    """
    Normalize the header row of the dataframe:
    - Trim excess spaces from column names
    - Convert column names to title case

    Args:
        file_path: Path to CSV file. If None, uses config.RAW_DATA_FILE (for CLI/script).

    Returns:
        DataFrame with normalized headers
    """
    try:
        path = str(file_path) if file_path is not None else str(config.RAW_DATA_FILE)
        df = read_csv(path)

        df_normalized = df.copy()
        new_columns: Dict[str, str] = {}

        for col in df_normalized.columns:
            trimmed_col = ' '.join(str(col).split())
            normalized_col = trimmed_col.title()
            new_columns[col] = normalized_col

        df_normalized.rename(columns=new_columns, inplace=True)

        return df_normalized
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to normalize headers: {e}") from e

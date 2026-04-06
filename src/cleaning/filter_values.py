from pathlib import Path
from typing import Optional, List, Tuple
import pandas as pd
import config
from csv_handler import read_csv


def filter_by_value(
    file_path: Optional[str | Path] = None,
    column: str = None,
    values: Optional[List] = None,
    value_range: Optional[Tuple[float, float]] = None,
) -> pd.DataFrame:
    """
    Filter DataFrame rows by column value.

    Supports two modes:
    - **values**: Keep rows where column value is in the given list.
    - **value_range**: Keep rows where column value is between min and max (inclusive).

    Args:
        file_path: Path to CSV file. If None, uses config.RAW_DATA_FILE.
        column: Column name to filter on.
        values: List of values to keep (categorical mode).
        value_range: Tuple of (min, max) to keep (numeric range mode).

    Returns:
        Filtered DataFrame.

    Raises:
        ValueError: If column is not found in the dataset.
    """
    try:
        path = str(file_path) if file_path is not None else str(config.RAW_DATA_FILE)
        df = read_csv(path)

        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found. Available: {list(df.columns)}")

        if value_range is not None:
            range_min, range_max = value_range
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            filtered = df[(numeric_col >= range_min) & (numeric_col <= range_max)]
            return filtered

        if not values:
            return df

        filtered = df[df[column].astype(str).isin([str(v) for v in values])]
        return filtered
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to filter by column '{column}': {e}") from e

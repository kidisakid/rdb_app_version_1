import country_converter as coco
import pandas as pd
import config
from csv_handler import read_csv


def standardize_country(column, file_path, convert_code) -> pd.DataFrame:
    """
    Args:
        column: Name of the column containing country names/codes to standardize.
        file_path: Path to CSV file. If None, uses config.RAW_DATA_FILE.
        convert_code: The format to convert country names/codes to.

    Returns:
        DataFrame with the specified column converted to ISO3 codes.
    """
    path = str(file_path) if file_path is not None else str(config.RAW_DATA_FILE)
    df = read_csv(path)
    df_standardized = df.copy()

    if column not in df_standardized.columns:
        raise ValueError(f"Column '{column}' not found in the dataset.")

    cc = coco.CountryConverter()
    col_idx = df_standardized.columns.get_loc(column) + 1
    df_standardized.insert(col_idx, "Country_Code", cc.pandas_convert(
        series=df_standardized[column], to=convert_code, not_found=None
    ))

    return df_standardized

import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import config
    CSV_ENCODINGS = config.CSV_ENCODINGS
    CSV_DELIMITERS = config.CSV_DELIMITERS
except ImportError:
    raise ImportError("config.py not found")


def read_csv(file_path: str) -> pd.DataFrame:
    """
    Attempts to read a CSV file using various encodings and delimiters.
    Falls back to Excel reading if CSV fails.

    Parameters:
        file_path (str): Path to the CSV (or xlsx) file.

    Returns:
        pd.DataFrame: Loaded data.

    Raises:
        ValueError: If the file cannot be read as CSV or Excel.
    """

    # Route Excel files directly to pd.read_excel() instead of attempting CSV parsing
    if str(file_path).lower().endswith(('.xlsx', '.xls')):
        try:
            return pd.read_excel(file_path)
        except Exception:
            raise ValueError(f"Unable to read Excel file: {file_path}")

    for enc in CSV_ENCODINGS:
        for sep in CSV_DELIMITERS:
            try:
                df = pd.read_csv(
                    file_path,
                    encoding=enc,
                    sep=sep,
                    on_bad_lines='skip',
                    engine='python'
                )
                if len(df.columns) > 1:
                    return df
            except (UnicodeDecodeError, pd.errors.ParserError, FileNotFoundError):
                continue

    raise ValueError(
        f"Unable to read {file_path} with tried encodings and delimiters."
    )


def write_csv(data: pd.DataFrame, file_path: str):
    """
    Writes a DataFrame to a CSV file without the index.

    Parameters:
        data (pd.DataFrame): Data to be written.
        file_path (str): Path to the output CSV file.
    """
    data.to_csv(file_path, index=False)


def append_csv(data: pd.DataFrame, file_path: str):
    """
    Appends a DataFrame to an existing CSV file, omitting the header.

    Parameters:
        data (pd.DataFrame): Data to append.
        file_path (str): Path to the target CSV file.
    """
    data.to_csv(file_path, mode='a', header=False, index=False)


def read_csv_to_dict(file_path: str) -> list[dict]:
    """
    Reads a CSV (or Excel) file and converts it to a list of dictionaries.

    Parameters:
        file_path (str): Path to the file.

    Returns:
        list[dict]: DataFrame records as list of dicts.
    """
    return read_csv(file_path).to_dict(orient='records')

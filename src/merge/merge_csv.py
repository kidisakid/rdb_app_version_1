"""
Merges multiple CSV or Excel files using a user-selected common column.
Rows are concatenated across all files and sorted by the chosen column.
"""
import pandas as pd
import config
from utils.csv_handler import read_csv


def _read_uploaded_file(uf):
    """Read a single Streamlit UploadedFile into a DataFrame.

    Returns None if the file cannot be parsed.
    """
    filename = uf.name
    suffix = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''

    if suffix not in ('csv', 'xlsx', 'xls'):
        return None

    uf.seek(0)

    if suffix in ('xlsx', 'xls'):
        try:
            return pd.read_excel(uf)
        except Exception:
            return None

    # CSV — try multiple encoding / delimiter combos
    for enc in config.CSV_ENCODINGS:
        for sep in config.CSV_DELIMITERS:
            uf.seek(0)
            try:
                candidate = pd.read_csv(
                    uf, encoding=enc, sep=sep, on_bad_lines='skip'
                )
                if len(candidate.columns) > 1:
                    return candidate
            except (UnicodeDecodeError, LookupError, pd.errors.ParserError):
                continue

    # Last-resort fallback
    uf.seek(0)
    return pd.read_csv(uf, on_bad_lines='skip')


def get_common_columns(uploaded_files):
    """Return the list of column names present in ALL uploaded files.

    Parameters
    ----------
    uploaded_files : list of UploadedFile
        Streamlit ``UploadedFile`` objects.

    Returns
    -------
    list[str]
        Column names common to every file, preserving the order they
        appear in the first file.
    """
    column_sets = []
    for uf in uploaded_files:
        df = _read_uploaded_file(uf)
        uf.seek(0)
        if df is not None:
            column_sets.append(set(df.columns))

    if not column_sets:
        return []

    common = column_sets[0]
    for cs in column_sets[1:]:
        common = common & cs

    # Preserve the column order from the first file
    first_df_cols = []
    df_first = _read_uploaded_file(uploaded_files[0])
    uploaded_files[0].seek(0)
    if df_first is not None:
        first_df_cols = [c for c in df_first.columns if c in common]
    return first_df_cols


def merge_csv(file_path=None, uploaded_files=None, merge_column=None):
    """Merge multiple CSV/Excel files using a common column.

    Parameters
    ----------
    file_path : str or None
        Unused (kept for pipeline convention). Falls back to
        ``config.RAW_DATA_FILE`` but multi-file merge requires
        *uploaded_files*.
    uploaded_files : list of UploadedFile, optional
        Streamlit ``UploadedFile`` objects to merge.
    merge_column : str or None
        Column name common to all files. Rows with null values in this
        column are dropped, and the result is sorted by this column.
    Returns
    -------
    pd.DataFrame
        Concatenated DataFrame sorted by *merge_column*.
    """
    file_path = file_path or config.RAW_DATA_FILE

    if not uploaded_files:
        df = read_csv(str(file_path))
        return df

    frames = []
    for uf in uploaded_files:
        df = _read_uploaded_file(uf)
        if df is not None:
            if merge_column and merge_column in df.columns:
                df = df.dropna(subset=[merge_column])
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    merged_df = pd.concat(frames, ignore_index=True, sort=False)

    if merge_column and merge_column in merged_df.columns:
        merged_df = merged_df.sort_values(by=merge_column, ignore_index=True)

    return merged_df

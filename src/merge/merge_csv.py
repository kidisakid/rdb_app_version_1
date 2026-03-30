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

    # Detect UTF-16 BOM and try that encoding first
    uf.seek(0)
    bom = uf.read(2)
    uf.seek(0)

    encodings = list(config.CSV_ENCODINGS)
    if bom in (b'\xff\xfe', b'\xfe\xff'):
        # Move utf-16 to the front so it's tried before latin1
        if 'utf-16' in encodings:
            encodings.remove('utf-16')
        encodings.insert(0, 'utf-16')

    # CSV — try multiple encoding / delimiter combos
    for enc in encodings:
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
    all_columns = []  # list of (ordered_cols, col_set) per file
    for uf in uploaded_files:
        df = _read_uploaded_file(uf)
        uf.seek(0)
        if df is not None:
            all_columns.append((list(df.columns), set(df.columns)))

    if not all_columns:
        return []

    common = all_columns[0][1]
    for _, cs in all_columns[1:]:
        common = common & cs

    # Preserve the column order from the first file
    return [c for c in all_columns[0][0] if c in common]


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

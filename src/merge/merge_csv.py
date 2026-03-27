"""
Merges multiple CSV or Excel files by country code (derived from the first
two characters of each filename).  Returns a single DataFrame with all rows
combined and a ``Country_Code`` column identifying the source group.
"""
import pandas as pd
import config
from utils.csv_handler import read_csv


def merge_csv(file_path=None, uploaded_files=None):
    """Merge multiple CSV/Excel files.

    Parameters
    ----------
    file_path : str or None
        Unused (kept for pipeline convention). Falls back to
        ``config.RAW_DATA_FILE`` but multi-file merge requires
        *uploaded_files*.
    uploaded_files : list of UploadedFile, optional
        Streamlit ``UploadedFile`` objects to merge.
    Returns
    -------
    pd.DataFrame
        Concatenated DataFrame.
    """
    file_path = file_path or config.RAW_DATA_FILE

    if not uploaded_files:
        df = read_csv(str(file_path))
        return df

    frames = []
    for uf in uploaded_files:
        filename = uf.name
        suffix = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''

        if suffix not in ('csv', 'xlsx', 'xls'):
            continue

        uf.seek(0)

        df = None

        if suffix in ('xlsx', 'xls'):
            try:
                df = pd.read_excel(uf)
            except Exception:
                continue
        else:
            for enc in config.CSV_ENCODINGS:
                for sep in config.CSV_DELIMITERS:
                    uf.seek(0)
                    try:
                        candidate = pd.read_csv(
                            uf, encoding=enc, sep=sep, on_bad_lines='skip'
                        )
                        if len(candidate.columns) > 1:
                            df = candidate
                            break
                    except (UnicodeDecodeError, LookupError, pd.errors.ParserError):
                        continue
                if df is not None:
                    break

            if df is None:
                uf.seek(0)
                df = pd.read_csv(uf, on_bad_lines='skip')

        if df is not None:
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    merged_df = pd.concat(frames, ignore_index=True, sort=False)
    return merged_df

"""
Streamlit UI for RDB data processing pipeline.
Upload CSV/Excel, select operations, preview, and download result.
"""

import sys
import tempfile
import warnings
from pathlib import Path

import pandas as pd
import streamlit as st

# Suppress terminal output from libraries when running in Streamlit
warnings.filterwarnings("ignore")

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.cleaning.normalize_headers import normalize_headers
from src.cleaning.removing_duplicates import remove_duplicates
from src.transformation.add_dates_metadata import add_dates_metadata
from src.transformation.translate_columns import translate_columns
from src.utils.csv_handler import read_csv

# --- Page config ---
st.set_page_config(
    page_title="Data Pipeline",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom styles ---
st.markdown(
    """
    <style>
    /* Header block */
    .main-header {
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-weight: 600;
        font-size: 1.75rem;
        color: #1a1a2e;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
    }
    .main-subtitle {
        font-size: 0.9rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    /* Section labels */
    .section-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #334155;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    [data-testid="stMarkdown"]:has(.section-title) {
        margin-top: 0.5rem;
    }

    /* ── File uploader ────────────────────────────── */
    [data-testid="stFileUploader"] section {
        padding: 3rem 2rem !important;
        border-radius: 10px !important;
        border: 1.5px dashed #cbd5e1 !important;
        background: #f8fafc !important;
    }

    @media (prefers-color-scheme: dark) {
        [data-testid="stFileUploader"] section {
            background: #1e2130 !important;
            border-color: #2d3248 !important;
        }
    }
    /* ────────────────────────────────────────────── */

    /* ── Metric cards ─────────────────────────────── */
    .status-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.1rem 1.25rem 1rem;
        position: relative;
        overflow: hidden;
        transition: box-shadow .2s, border-color .2s;
    }
    .status-box:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 16px rgba(26, 26, 46, .07);
    }
    .status-box::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        border-radius: 10px 10px 0 0;
    }
    .status-box.rows::before { background: #1a1a2e; }
    .status-box.cols::before { background: #334155; }
    .status-box.size::before { background: #64748b; }

    .status-icon {
        font-size: .72rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: .08em;
        font-weight: 600;
        margin-bottom: .35rem;
    }
    .status-val {
        font-size: 1.75rem;
        font-weight: 700;
        line-height: 1;
        color: #1a1a2e;
        letter-spacing: -.02em;
        margin-bottom: .3rem;
    }
    .status-lbl {
        font-size: .78rem;
        color: #64748b;
        font-weight: 500;
    }

    /* ── Dark mode overrides ──────────────────────── */
    @media (prefers-color-scheme: dark) {
        .status-box {
            background: #1e2130;
            border-color: #2d3248;
        }
        .status-box:hover {
            border-color: #3d4460;
            box-shadow: 0 4px 16px rgba(0, 0, 0, .3);
        }
        .status-box.rows::before { background: #a5b4fc; }
        .status-box.cols::before { background: #7dd3fc; }
        .status-box.size::before { background: #94a3b8; }
        .status-val  { color: #f1f5f9; }
        .status-lbl  { color: #94a3b8; }
        .status-icon { color: #475569; }
    }
    /* ────────────────────────────────────────────── */

    /* Hide Streamlit branding; keep sidebar toggle visible */
    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
    header[data-testid="stHeader"] {
        background: transparent !important;
        box-shadow: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def detect_encoding(uploaded_file) -> str:
    """Detect encoding by trying each entry in config.CSV_ENCODINGS in order."""
    raw = uploaded_file.read(50_000)
    uploaded_file.seek(0)
    for enc in config.CSV_ENCODINGS:
        try:
            raw.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return config.CSV_ENCODINGS[0]


def load_uploaded_file(uploaded_file) -> tuple[pd.DataFrame, str]:
    """Load CSV or Excel. Returns (dataframe, encoding_used)."""
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(uploaded_file), "n/a"
    if suffix == ".csv":
        encoding = detect_encoding(uploaded_file)
        return (
            pd.read_csv(uploaded_file, encoding=encoding, on_bad_lines="skip"),
            encoding,
        )
    raise ValueError("Unsupported format. Use CSV or Excel (.xlsx, .xls).")


def run_pipeline(
    temp_path: str,
    steps: list,
    dup_columns: list | None,
    translate_columns_list: list | None,
    target_lang: str,
    source_lang: str,
    progress_placeholder,
) -> pd.DataFrame | None:
    """Run selected pipeline steps; update progress; return final DataFrame or None on error."""
    df = None
    n = len(steps)
    for i, step in enumerate(steps):
        p = (i + 1) / n
        progress_placeholder.progress(p, text=f"Running: {step}")
        try:
            if step == "Normalize headers":
                df = normalize_headers(file_path=temp_path)
            elif step == "Remove duplicates":
                df = remove_duplicates(
                    columns=dup_columns if dup_columns else None,
                    file_path=temp_path,
                )
            elif step == "Add date metadata":
                df = add_dates_metadata(file_path=temp_path)
            elif step == "Translate columns":
                def _translate_progress(current: int, total: int, message: str) -> None:
                    p = (i + (current / total if total else 0)) / n
                    progress_placeholder.progress(max(0.0, min(1.0, p)), text=message)
                try:
                    df = translate_columns(
                        target_language=target_lang,
                        source_language=source_lang,
                        columns_to_process=translate_columns_list,
                        file_path=temp_path,
                        progress_callback=_translate_progress,
                    )
                except TypeError:
                    df = translate_columns(
                        target_language=target_lang,
                        source_language=source_lang,
                        columns_to_process=translate_columns_list,
                        file_path=temp_path,
                    )
            else:
                continue
            # After first step, write df so next step reads updated data
            if i < n - 1 and df is not None:
                df.to_csv(temp_path, index=False)
        except Exception as e:
            progress_placeholder.progress(1.0, text="Error")
            st.error(str(e))
            return None
    progress_placeholder.progress(1.0, text="Done")
    return df


def main():
    st.markdown('<p class="main-header">Data Pipeline</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="main-subtitle">Upload a CSV or Excel file, choose operations, preview, and download the result.</p>',
        unsafe_allow_html=True,
    )

    # --- Sidebar: process selection ---
    st.sidebar.markdown('<p class="section-title">Process</p>', unsafe_allow_html=True)
    all_options = [
        "Normalize headers",
        "Remove duplicates",
        "Add date metadata",
        "Translate columns",
    ]
    run_all = st.sidebar.checkbox("Run all steps", value=False)
    if run_all:
        selected_steps = all_options.copy()
    else:
        selected_steps = st.sidebar.multiselect(
            "Select steps to run",
            options=all_options,
            default=[],
        )

    # --- Main: file upload ---
    st.markdown('<p class="section-title">Input</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
    )

    if not uploaded_file:
        st.info("Upload a file to begin.")
        return

    try:
        input_df, _ = load_uploaded_file(uploaded_file)
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return

    # ── Metric cards ──────────────────────────────────────────────────────────
    row_count  = len(input_df)
    col_count  = len(input_df.columns)

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown(
            f"""<div class="status-box rows">
                  <div class="status-icon">Rows</div>
                  <div class="status-val">{row_count:,}</div>
                  <div class="status-lbl">Total records in file</div>
                </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div class="status-box cols">
                  <div class="status-icon">Columns</div>
                  <div class="status-val">{col_count}</div>
                  <div class="status-lbl">Fields detected</div>
                </div>""",
            unsafe_allow_html=True,
        )

    st.divider()
    st.dataframe(input_df.head(5), use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────

    # --- Options for selected steps ---
    col_names = list(input_df.columns)
    dup_columns = None
    translate_columns_list = None
    target_lang = "en"
    source_lang = "auto"

    if "Remove duplicates" in selected_steps:
        st.sidebar.markdown("**Remove duplicates**")
        dup_columns = st.sidebar.multiselect(
            "Columns to check",
            col_names,
            key="dup_cols",
        )

    if "Translate columns" in selected_steps:
        st.sidebar.markdown("**Translate columns**")
        translate_columns_list = st.sidebar.multiselect(
            "Columns to translate",
            col_names,
            key="trans_cols",
        )
        target_lang = st.sidebar.text_input("Target language code", value="en", key="target_lang")
        source_lang = st.sidebar.text_input("Source language code", value="auto", key="source_lang")

    # --- Run ---
    st.markdown('<p class="section-title">Run</p>', unsafe_allow_html=True)
    run_clicked = st.button("Run pipeline")

    if run_clicked and not selected_steps:
        st.warning("Select at least one process step.")
        return

    if run_clicked and selected_steps and "Remove duplicates" in selected_steps and dup_columns is not None and len(dup_columns) == 0:
        st.warning("Please select at least one column to check for duplicates.")
        return
    if run_clicked and selected_steps and "Translate columns" in selected_steps and (not translate_columns_list or len(translate_columns_list) == 0):
        st.warning("Please select at least one column to translate.")
        return

    if run_clicked and selected_steps:
        progress_placeholder = st.empty()
        fd, tmp_path = tempfile.mkstemp(suffix=".csv")
        try:
            with open(fd, "w", encoding="utf-8", newline="") as f:
                input_df.to_csv(f, index=False)
            trans_cols = translate_columns_list if "Translate columns" in selected_steps else None
            result_df = run_pipeline(
                tmp_path,
                selected_steps,
                dup_columns,
                trans_cols,
                target_lang,
                source_lang,
                progress_placeholder,
            )
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except OSError:
                pass

        if result_df is None:
            return

        # --- Preview ---
        st.markdown('<p class="section-title">Preview</p>', unsafe_allow_html=True)
        st.dataframe(result_df.head(100), use_container_width=True)
        st.caption(f"Showing first 100 of {len(result_df):,} rows.")

        # --- Download ---
        st.markdown('<p class="section-title">Download</p>', unsafe_allow_html=True)
        out_format = st.radio("Format", ["CSV", "Excel"], horizontal=True, key="out_fmt")
        base_name = Path(uploaded_file.name).stem
        if out_format == "CSV":
            out_name = f"{base_name}_processed.csv"
            out_bytes = result_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download CSV",
                data=out_bytes,
                file_name=out_name,
                mime="text/csv",
            )
        else:
            out_name = f"{base_name}_processed.xlsx"
            buf = __import__("io").BytesIO()
            result_df.to_excel(buf, index=False, engine="openpyxl")
            buf.seek(0)
            st.download_button(
                label="Download Excel",
                data=buf.getvalue(),
                file_name=out_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


if __name__ == "__main__":
    main()

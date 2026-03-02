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
    /* Section cards */
    .section-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #334155;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    /* Metrics / status */
    .status-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        font-size: 0.875rem;
        color: #475569;
    }
    /* Hide Streamlit branding for cleaner look; keep header so top-left << sidebar toggle stays visible */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Load CSV or Excel from uploaded file."""
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(uploaded_file, encoding="utf-8", on_bad_lines="skip")
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(uploaded_file)
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
                    progress_placeholder.progress(p, text=message)
                df = translate_columns(
                    target_language=target_lang,
                    source_language=source_lang,
                    columns_to_process=translate_columns_list,
                    file_path=temp_path,
                    progress_callback=_translate_progress,
                )
            else:
                continue
            # After first step, subsequent steps read from file; write current df so next step sees it
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
        input_df = load_uploaded_file(uploaded_file)
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return

    st.markdown(
        f'<div class="status-box">Rows: {len(input_df):,} | Columns: {len(input_df.columns):,}</div>',
        unsafe_allow_html=True,
    )

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

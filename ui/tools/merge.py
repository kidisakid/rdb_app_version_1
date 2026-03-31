"""
Merge Data tool — combine multiple CSV/Excel files into one.
"""

import pandas as pd
import streamlit as st

from src.merge.merge_csv import merge_csv, get_common_columns
from ui.helpers import render_download


def _load_file_manifest(uploaded_files: list) -> pd.DataFrame:
    """Build a summary table of uploaded files with row and column counts."""
    rows = []
    for uf in uploaded_files:
        uf.seek(0)
        try:
            suffix = uf.name.lower().rsplit('.', 1)[-1] if '.' in uf.name else ''
            if suffix in ('xlsx', 'xls'):
                df_peek = pd.read_excel(uf)
            else:
                df_peek = pd.read_csv(uf, on_bad_lines="skip", nrows=None)
            n_rows = len(df_peek)
            n_cols = len(df_peek.columns)
        except Exception:
            n_rows = "?"
            n_cols = "?"
        uf.seek(0)
        rows.append({
            "Filename": uf.name,
            "Rows": n_rows,
            "Columns": n_cols,
        })
    return pd.DataFrame(rows)


def tool_merge_csv():
    st.markdown("""
    <div class="page-hero">
        <div class="hero-eyebrow">Media Intelligence Platform</div>
        <p class="main-header">Merge Data</p>
        <p class="main-subtitle">Combine multiple CSV or Excel files into a single dataset.</p>
        <div class="hero-actions">
            <span class="hero-badge"><span class="hero-badge-dot"></span>Ready</span>
            <span class="hero-badge">Multi-file</span>
            <span class="hero-badge">CSV &amp; Excel</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── File upload (multi) ──────────────────────────────────────────
    st.markdown(
        '<div class="section-divider">'
        '<span class="section-divider-label">Input</span>'
        '<span class="section-divider-line"></span></div>',
        unsafe_allow_html=True,
    )
    uploaded_files = st.file_uploader(
        "Upload CSV or Excel files to merge",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="merge_uploader",
    )

    if not uploaded_files or len(uploaded_files) < 2:
        st.markdown("""
        <div style="font-family:'DM Sans',sans-serif;font-size:0.82rem;color:#94a3b8;
             text-align:center;padding:1rem 0;letter-spacing:0.01em;">
            Drop at least 2 files above to begin merging (CSV, XLSX, XLS)
        </div>
        """, unsafe_allow_html=True)
        return

    # ── File manifest ────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider">'
        '<span class="section-divider-label">File Summary</span>'
        '<span class="section-divider-line"></span></div>',
        unsafe_allow_html=True,
    )

    manifest_df = _load_file_manifest(uploaded_files)
    st.dataframe(manifest_df, use_container_width=True, hide_index=True)

    total_rows = manifest_df["Rows"].apply(pd.to_numeric, errors="coerce").sum()
    total_cols = manifest_df["Columns"].apply(pd.to_numeric, errors="coerce").max()
    rows_display = f"{int(total_rows):,}" if pd.notna(total_rows) else "?"
    cols_display = f"{int(total_cols):,}" if pd.notna(total_cols) else "?"
    st.markdown(
        f'<p style="font-family:DM Sans,sans-serif;font-size:0.82rem;color:#64748b;">'
        f'When merged: {rows_display} total rows &middot; {cols_display} columns</p>',
        unsafe_allow_html=True,
    )

    # ── Common column selection ──────────────────────────────────────
    st.markdown(
        '<div class="section-divider">'
        '<span class="section-divider-label">Merge Column</span>'
        '<span class="section-divider-line"></span></div>',
        unsafe_allow_html=True,
    )

    common_cols = get_common_columns(uploaded_files)

    if not common_cols:
        st.error(
            "No common columns found across all uploaded files. "
            "Please ensure the files share at least one column name."
        )
        return

    merge_column = st.selectbox(
        "Select a column common to all files to merge on",
        options=common_cols,
        key="merge_column_select",
    )

    # ── Merge ────────────────────────────────────────────────────────
    merge_clicked = st.button("Merge Files", type="primary", use_container_width=False)

    if merge_clicked:
        progress = st.empty()
        progress.progress(0.5, text="Merging files...")

        try:
            result_df = merge_csv(
                uploaded_files=uploaded_files, merge_column=merge_column
            )
            progress.progress(1.0, text="Done")
            st.session_state["merge_result_df"] = result_df
        except Exception as e:
            progress.progress(1.0, text="Error")
            st.error(str(e))
            return

    if "merge_result_df" in st.session_state:
        result_df = st.session_state["merge_result_df"]

        # ── Download ─────────────────────────────────────────────────
        render_download(result_df, "merged_data")

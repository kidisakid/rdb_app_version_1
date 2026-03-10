"""
Streamlit UI for RDB data processing pipeline.
Upload CSV/Excel, select operations, preview, and download result.
"""

import sys
import tempfile
import warnings
import io
from pathlib import Path

import pandas as pd
import streamlit as st

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.cleaning.normalize_headers import normalize_headers
from src.cleaning.removing_duplicates import remove_duplicates
from src.transformation.add_dates_metadata import add_dates_metadata
from src.transformation.translate_columns import translate_columns
from config import STEP_REGISTRY, ALL_LABELS, GROUP_CONFIG, GROUP_DARK_BG, GROUP_DARK_COLOR


# Page config
st.set_page_config(
    page_title="Data Pipeline",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styles
from styles import STYLES
st.markdown(STYLES, unsafe_allow_html=True)


# Helpers (use GROUP_CONFIG from config.py)
def get_group_color(group: str) -> str:
    return GROUP_CONFIG.get(group, {}).get("color", "#94a3b8")

def get_group_bg(group: str) -> str:
    return GROUP_CONFIG.get(group, {}).get("bg", "#f8fafc")




# SVG icons per group
GROUP_ICONS = {
    "Cleaning": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><polyline points="19 6 18 20 6 20 5 6"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>',
    "Enrichment": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>',
}


# Sidebar
def render_sidebar(col_names: list) -> tuple:
    st.sidebar.markdown('<p class="sidebar-header">Pipeline Process</p>', unsafe_allow_html=True)

    search = st.sidebar.text_input("🔍 Search steps", placeholder="Search step", label_visibility="collapsed")
    run_all = st.sidebar.checkbox("Run all steps", value=False)

    groups: dict[str, list] = {}
    for step in STEP_REGISTRY:
        if search.lower() in step["label"].lower():
            groups.setdefault(step["group"], []).append(step)

    selected_labels = []

    for group_name, group_steps in groups.items():
        color = get_group_color(group_name)
        bg = get_group_bg(group_name)

        selected_in_group = [s for s in group_steps if st.session_state.get(s["id"], False)]
        n_sel = len(selected_in_group)
        all_checked = n_sel == len(group_steps)

        open_key = f"open_{group_name}"
        if open_key not in st.session_state:
            st.session_state[open_key] = False
        is_open = st.session_state[open_key] or run_all

        # ── Category row: expander only ─────────────────────────────────
        count_txt = f" {n_sel}/{len(group_steps)}" if n_sel else ""

        with st.sidebar.expander(f"{group_name}{count_txt}", expanded=is_open):
                # Sync open state
                st.session_state[open_key] = True

                # Select-all toggle
                def _toggle_group(gname=group_name, gsteps=group_steps):
                    currently_all = all(st.session_state.get(s["id"], False) for s in gsteps)
                    for s in gsteps:
                        st.session_state[s["id"]] = not currently_all

                selall_lbl = "✕ Deselect all" if all_checked else "✓ Select all"
                st.button(selall_lbl, key=f"selall_{group_name}", on_click=_toggle_group)

                # Individual steps as checkboxes
                for step in group_steps:
                    checked = st.checkbox(
                        step["label"],
                        key=step["id"],
                        value=run_all or st.session_state.get(step["id"], False),
                        disabled=run_all,
                    )
                    if checked or run_all:
                        selected_labels.append(step["label"])

    # Per-step options
    dup_columns = None
    translate_cols_list = None
    target_lang = "en"
    source_lang = "auto"

    if "Remove duplicates" in selected_labels:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Remove duplicates — options**")
        dup_columns = st.sidebar.multiselect("Columns to check", col_names, key="dup_cols")

    if "Translate columns" in selected_labels:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Translate columns — options**")
        translate_cols_list = st.sidebar.multiselect("Columns to translate", col_names, key="trans_cols")
        target_lang = st.sidebar.text_input("Target language code", value="en", key="target_lang")
        source_lang = st.sidebar.text_input("Source language code", value="auto", key="source_lang")

    return selected_labels, dup_columns, translate_cols_list, target_lang, source_lang


# Pipeline strip builder
def render_pipeline_strip(selected_steps: list):
    if not selected_steps:
        return
    chips = []
    for i, label in enumerate(selected_steps):
        step = next((s for s in STEP_REGISTRY if s["label"] == label), None)
        group = step["group"] if step else "Cleaning"
        color = get_group_color(group)
        bg = get_group_bg(group)
        chips.append(
            f'<span class="pipeline-chip" style="background:{bg};color:{color};border:1px solid {color}44">'
            f'{label}</span>'
        )
        if i < len(selected_steps) - 1:
            chips.append('<span class="pipeline-arrow">→</span>')

    st.markdown(
        '<div class="pipeline-strip"><span class="pipeline-label">Pipeline:</span>'
        + "".join(chips) + '</div>',
        unsafe_allow_html=True,
    )


# File helpers
def detect_encoding(uploaded_file) -> str:
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


# Pipeline runner
def run_pipeline(
    temp_path: str,
    steps: list,
    dup_columns: list | None,
    translate_columns_list: list | None,
    target_lang: str,
    source_lang: str,
    progress_placeholder,
) -> pd.DataFrame | None:
    df = None
    n = len(steps)
    for i, step in enumerate(steps):
        progress_placeholder.progress((i + 1) / n, text=f"Running: {step}")
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
                    pct = (i + (current / total if total else 0)) / n
                    progress_placeholder.progress(max(0.0, min(1.0, pct)), text=message)
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

            if i < n - 1 and df is not None:
                df.to_csv(temp_path, index=False)

        except Exception as e:
            progress_placeholder.progress(1.0, text="Error")
            st.error(str(e))
            return None

    progress_placeholder.progress(1.0, text="Done")
    return df


# Main
def main():
    # ── Hero header ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="page-hero">
        <div class="hero-eyebrow">Media Intelligence Platform</div>
        <p class="main-header">Data Pipeline</p>
        <p class="main-subtitle">Transform raw media data into clean, enriched datasets ready for analysis.</p>
        <div class="hero-actions">
            <span class="hero-badge"><span class="hero-badge-dot"></span>Ready</span>
            <span class="hero-badge">📁 CSV &amp; Excel</span>
            <span class="hero-badge">⚡ 4 operations</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── File upload ──────────────────────────────────────────────────────
    st.markdown('<div class="section-divider"><span class="section-divider-label">Input</span><span class="section-divider-line"></span></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
    )

    if not uploaded_file:
        st.markdown("""
        <div style="font-family:'DM Sans',sans-serif;font-size:0.82rem;color:#94a3b8;
             text-align:center;padding:1rem 0;letter-spacing:0.01em;">
            Drop a file above to begin — supports CSV, XLSX, XLS up to 200MB
        </div>
        """, unsafe_allow_html=True)
        return

    try:
        input_df, _ = load_uploaded_file(uploaded_file)
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return

    col_names = list(input_df.columns)
    selected_steps, dup_columns, translate_cols_list, target_lang, source_lang = render_sidebar(col_names)

    # ── Metric cards ─────────────────────────────────────────────────────
    st.markdown('<div class="section-divider"><span class="section-divider-label">Dataset Overview</span><span class="section-divider-line"></span></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown(f"""
        <div class="status-box rows">
            <div class="status-box-glow"></div>
            <div class="status-icon">Rows</div>
            <div class="status-val">{len(input_df):,}</div>
            <div class="status-lbl">Total records</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="status-box cols">
            <div class="status-box-glow"></div>
            <div class="status-icon">Columns</div>
            <div class="status-val">{len(input_df.columns)}</div>
            <div class="status-lbl">Fields detected</div>
        </div>""", unsafe_allow_html=True)

    # ── Data preview ─────────────────────────────────────────────────────
    st.markdown('<div class="section-divider" style="margin-top:1.25rem"><span class="section-divider-label">Preview</span><span class="section-divider-line"></span></div>', unsafe_allow_html=True)
    st.dataframe(input_df.head(5), use_container_width=True, height=220)

    # ── Pipeline strip + Run ─────────────────────────────────────────────
    if selected_steps:
        render_pipeline_strip(selected_steps)

    st.markdown('<div class="section-divider"><span class="section-divider-label">Execute</span><span class="section-divider-line"></span></div>', unsafe_allow_html=True)
    run_clicked = st.button("▶  Run Pipeline", type="primary", disabled=not selected_steps, use_container_width=False)

    if not selected_steps:
        st.markdown('<p style="font-family:DM Sans,sans-serif;font-size:0.78rem;color:#94a3b8;margin-top:0.25rem">Select at least one pipeline step from the sidebar to begin.</p>', unsafe_allow_html=True)

    if run_clicked and "Remove duplicates" in selected_steps and not dup_columns:
        st.warning("Please select at least one column to check for duplicates.")
        return
    if run_clicked and "Translate columns" in selected_steps and not translate_cols_list:
        st.warning("Please select at least one column to translate.")
        return

    if run_clicked and selected_steps:
        progress_placeholder = st.empty()
        fd, tmp_path = tempfile.mkstemp(suffix=".csv")
        try:
            with open(fd, "w", encoding="utf-8", newline="") as f:
                input_df.to_csv(f, index=False)
            result_df = run_pipeline(
                tmp_path, selected_steps, dup_columns,
                translate_cols_list if "Translate columns" in selected_steps else None,
                target_lang, source_lang, progress_placeholder,
            )
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except OSError:
                pass

        if result_df is None:
            return

        # ── Results ──────────────────────────────────────────────────────
        st.markdown('<div class="section-divider" style="margin-top:1.5rem"><span class="section-divider-label">Results</span><span class="section-divider-line"></span></div>', unsafe_allow_html=True)

        r1, r2 = st.columns(2, gap="medium")
        with r1:
            st.markdown(f"""
            <div class="status-box rows">
                <div class="status-box-glow"></div>
                <div class="status-icon">Output Rows</div>
                <div class="status-val">{len(result_df):,}</div>
                <div class="status-lbl">Records after processing</div>
            </div>""", unsafe_allow_html=True)
        with r2:
            delta = len(input_df) - len(result_df)
            sign = "−" if delta > 0 else "+"
            st.markdown(f"""
            <div class="status-box cols">
                <div class="status-box-glow"></div>
                <div class="status-icon">Delta</div>
                <div class="status-val">{sign}{abs(delta):,}</div>
                <div class="status-lbl">Rows {"removed" if delta > 0 else "added"}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div style="margin-top:1rem"></div>', unsafe_allow_html=True)
        st.dataframe(result_df.head(100), use_container_width=True)
        st.caption(f"Showing first 100 of {len(result_df):,} rows.")

        # ── Download ──────────────────────────────────────────────────────
        st.markdown('<div class="section-divider" style="margin-top:1rem"><span class="section-divider-label">Download</span><span class="section-divider-line"></span></div>', unsafe_allow_html=True)
        out_format = st.radio("Format", ["CSV", "Excel"], horizontal=True, key="out_fmt")
        base_name = Path(uploaded_file.name).stem

        if out_format == "CSV":
            st.download_button(
                label="⬇  Download CSV",
                data=result_df.to_csv(index=False).encode("utf-8"),
                file_name=f"{base_name}_processed.csv",
                mime="text/csv",
            )
        else:
            buf = io.BytesIO()
            result_df.to_excel(buf, index=False, engine="openpyxl")
            buf.seek(0)
            st.download_button(
                label="⬇  Download Excel",
                data=buf.getvalue(),
                file_name=f"{base_name}_processed.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


if __name__ == "__main__":
    main()
"""
Streamlit UI for RDB data processing pipeline.
Upload CSV/Excel, select operations, preview, and download result.
"""

import sys
import tempfile
import warnings
import io
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.cleaning.normalize_headers import normalize_headers
from src.cleaning.removing_duplicates import remove_duplicates
from src.transformation.add_dates_metadata import add_dates_metadata
from src.transformation.translate_columns import translate_columns
from src.clustering.topic_clustering import topic_cluster, TopicClusterer, clean_text
from src.merge.merge_csv import merge_csv
from config import STEP_REGISTRY, GROUP_CONFIG


# Page config
st.set_page_config(
    page_title="Data Pipeline",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styles
from styles import STYLES
st.markdown(STYLES, unsafe_allow_html=True)


def get_group_color(group: str) -> str:
    return GROUP_CONFIG.get(group, {}).get("color", "#94a3b8")

def get_group_bg(group: str) -> str:
    return GROUP_CONFIG.get(group, {}).get("bg", "#f8fafc")

# Sidebar
def render_sidebar(col_names: list, file_count: int = 1) -> tuple:
    st.sidebar.markdown('<p class="sidebar-header">Pipeline Process</p>', unsafe_allow_html=True)

    search = st.sidebar.text_input("🔍 Search steps", placeholder="Search step", label_visibility="collapsed")
    run_all = st.sidebar.checkbox("Run all steps", value=False)

    groups: dict[str, list] = {}
    for step in STEP_REGISTRY:
        groups.setdefault(step["group"], []).append(step)

    # ── Select all / Deselect all ───────────────────────────────────
    all_checked = all(st.session_state.get(s["id"], False) for s in STEP_REGISTRY)

    def _toggle_all():
        new_val = not all(st.session_state.get(s["id"], False) for s in STEP_REGISTRY)
        for s in STEP_REGISTRY:
            st.session_state[s["id"]] = new_val

    st.sidebar.button(
        "Deselect all" if all_checked else "Select all",
        key="select_all_btn",
        on_click=_toggle_all,
        use_container_width=True,
    )

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
                    min_files = step.get("min_files", 1)
                    step_blocked = file_count < min_files

                    # Force-uncheck steps that can't run with current file count
                    if step_blocked and st.session_state.get(step["id"], False):
                        st.session_state[step["id"]] = False

                    checked = st.checkbox(
                        step["label"],
                        key=step["id"],
                        value=(not step_blocked) and (run_all or st.session_state.get(step["id"], False)),
                        disabled=run_all or step_blocked,
                        help=f"Requires at least {min_files} files" if step_blocked else None,
                    )
                    if (checked or run_all) and not step_blocked:
                        selected_labels.append(step["label"])

    # ── Per-step options (only appear when relevant) ────────────────
    dup_columns = None
    translate_cols_list = None
    target_lang = "en"
    source_lang = "auto"

    if "Remove duplicates" in selected_labels:
        st.sidebar.caption("Requires: Remove duplicates")
        dup_columns = st.sidebar.multiselect("Columns to check", col_names, key="dup_cols")

    if "Translate columns" in selected_labels:
        st.sidebar.caption("Requires: Translate columns")
        translate_cols_list = st.sidebar.multiselect("Columns to translate", col_names, key="trans_cols")
        col1, col2 = st.sidebar.columns(2, gap="small")
        target_lang = col1.text_input("Target", value="en", key="target_lang")
        source_lang = col2.text_input("Source", value="auto", key="source_lang")

    # Topic clustering options
    cluster_params = None
    if "Topic clustering" in selected_labels:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Topic clustering — options**")
        text_cols = [c for c in col_names]
        cluster_text_col = st.sidebar.selectbox("Text column to cluster", text_cols, key="cluster_text_col")
        cluster_n = st.sidebar.slider("Number of clusters", 2, 20, 5, key="cluster_n")
        cluster_max_df = st.sidebar.slider("Max document frequency", 0.1, 1.0, 0.95, 0.05, key="cluster_max_df")
        cluster_min_df = st.sidebar.slider("Min document frequency", 1, 10, 1, key="cluster_min_df")
        cluster_n_init = st.sidebar.slider("K-Means initializations", 1, 20, 10, key="cluster_n_init")
        cluster_clean = st.sidebar.checkbox("Clean text before clustering", value=True, key="cluster_clean")
        cluster_params = {
            "text_column": cluster_text_col,
            "n_clusters": cluster_n,
            "max_df": cluster_max_df,
            "min_df": cluster_min_df,
            "n_init": cluster_n_init,
            "clean_text_option": cluster_clean,
        }

    return selected_labels, dup_columns, translate_cols_list, target_lang, source_lang, cluster_params


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
        for enc in config.CSV_ENCODINGS:
            for sep in config.CSV_DELIMITERS:
                uploaded_file.seek(0)
                try:
                    df = pd.read_csv(
                        uploaded_file, encoding=enc, sep=sep, on_bad_lines="skip",
                    )
                    if len(df.columns) > 1:
                        return df, enc
                except (UnicodeDecodeError, LookupError, pd.errors.ParserError):
                    continue
        # Last resort: default read
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, on_bad_lines="skip"), "utf-8"
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
    cluster_params: dict | None = None,
    merge_files: list | None = None,
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

            elif step == "Merge CSV files":
                df = merge_csv(
                    file_path=temp_path,
                    uploaded_files=merge_files,
                )

            elif step == "Topic clustering":
                params = cluster_params or {}
                df = topic_cluster(
                    file_path=temp_path,
                    text_column=params.get("text_column"),
                    n_clusters=params.get("n_clusters", 5),
                    max_df=params.get("max_df", 0.95),
                    min_df=params.get("min_df", 1),
                    n_init=params.get("n_init", 10),
                    clean_text_option=params.get("clean_text_option", True),
                )
                # Store clusterer for visualizations
                if hasattr(df, 'attrs') and 'clusterer' in df.attrs:
                    st.session_state['_clusterer'] = df.attrs['clusterer']
                    st.session_state['_cluster_text_col'] = df.attrs.get('cluster_text_column')
                    st.session_state['_cluster_n'] = params.get("n_clusters", 5)

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
            <span class="hero-badge">⚡ 6 operations</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── File upload ──────────────────────────────────────────────────────
    st.markdown('<div class="section-divider"><span class="section-divider-label">Input</span><span class="section-divider-line"></span></div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if not uploaded_files:
        st.markdown("""
        <div style="font-family:'DM Sans',sans-serif;font-size:0.82rem;color:#94a3b8;
             text-align:center;padding:1rem 0;letter-spacing:0.01em;">
            Drop files above to begin — supports CSV, XLSX, XLS up to 200MB
        </div>
        """, unsafe_allow_html=True)
        return

    file_count = len(uploaded_files)

    # Load the first file for preview and single-file pipeline steps
    try:
        input_df, _ = load_uploaded_file(uploaded_files[0])
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return

    col_names = list(input_df.columns)
    selected_steps, dup_columns, translate_cols_list, target_lang, source_lang, cluster_params = render_sidebar(col_names, file_count=file_count)

    # ── File info ─────────────────────────────────────────────────────────
    if file_count > 1:
        st.info(f"{file_count} files uploaded — multi-file steps (e.g. Merge) are now available. "
                f"Previewing: **{uploaded_files[0].name}**")

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
                cluster_params=cluster_params if "Topic clustering" in selected_steps else None,
                merge_files=uploaded_files if "Merge CSV files" in selected_steps else None,
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
        base_name = Path(uploaded_files[0].name).stem

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

        # ── Topic Clustering Visualizations ──────────────────────────────
        if "Topic clustering" in selected_steps and st.session_state.get('_clusterer'):
            display_clustering_visualizations(result_df)


def display_clustering_visualizations(result_df: pd.DataFrame):
    """Display full clustering visualizations after pipeline run."""
    clusterer = st.session_state.get('_clusterer')
    text_column = st.session_state.get('_cluster_text_col')
    n_clusters = st.session_state.get('_cluster_n', 5)

    if clusterer is None or 'Cluster_Topic' not in result_df.columns:
        return

    st.markdown('<div class="section-divider" style="margin-top:1.5rem"><span class="section-divider-label">Clustering Analysis</span><span class="section-divider-line"></span></div>', unsafe_allow_html=True)

    # ── Cluster Distribution + Top Terms ─────────────────────────────
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("**Cluster Distribution**")
        cluster_counts = result_df['Cluster_Topic'].value_counts().sort_index()
        st.dataframe(cluster_counts.rename('Count'), use_container_width=True)

    with col2:
        st.bar_chart(result_df['Cluster_Topic'].value_counts().sort_index())

    st.divider()

    # ── Top Terms per Cluster ────────────────────────────────────────
    st.markdown("**Top Terms per Cluster**")
    top_terms = clusterer.get_top_terms(n_terms=10)
    cols = st.columns(min(3, n_clusters))
    for cluster_id in range(n_clusters):
        with cols[cluster_id % len(cols)]:
            terms = top_terms.get(cluster_id, [])
            st.markdown(f"**Cluster {cluster_id}**")
            for i, term in enumerate(terms[:5], 1):
                st.write(f"{i}. {term}")

    st.divider()

    # ── PCA Scatter Plot + Pie Chart ─────────────────────────────────
    st.markdown("**Cluster Visualizations**")
    viz1, viz2 = st.columns(2)

    with viz1:
        try:
            texts = result_df[text_column].tolist() if text_column else None
            coordinates_2d, clusters = clusterer.get_2d_coordinates(texts)

            fig, ax = plt.subplots(figsize=(8, 6))
            colors = plt.cm.get_cmap('tab20')(np.linspace(0, 1, n_clusters))

            for cid in range(n_clusters):
                mask = clusters == cid
                ax.scatter(
                    coordinates_2d[mask, 0], coordinates_2d[mask, 1],
                    c=[colors[cid]], label=f'Cluster {cid}',
                    alpha=0.6, s=80, edgecolors='black', linewidth=0.5,
                )

            ax.set_xlabel('PC 1', fontsize=11)
            ax.set_ylabel('PC 2', fontsize=11)
            ax.set_title('Cluster Distribution (PCA)', fontsize=13, fontweight='bold')
            ax.legend(fontsize=8, loc='best')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
        except Exception as e:
            st.error(f"PCA visualization error: {e}")

    with viz2:
        try:
            cluster_counts = result_df['Cluster_Topic'].value_counts().sort_index()
            fig, ax = plt.subplots(figsize=(8, 6))
            colors_pie = plt.cm.get_cmap('tab20')(np.linspace(0, 1, n_clusters))
            wedges, texts_pie, autotexts = ax.pie(
                cluster_counts,
                labels=[f'Cluster {i}' for i in cluster_counts.index],
                autopct='%1.1f%%',
                colors=colors_pie[:len(cluster_counts)],
                startangle=90,
                textprops={'fontsize': 9},
            )
            for at in autotexts:
                at.set_color('white')
                at.set_fontweight('bold')
                at.set_fontsize(8)
            ax.set_title('Cluster Size Distribution', fontsize=13, fontweight='bold')
            plt.tight_layout()
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Pie chart error: {e}")

    st.divider()

    # ── Top Terms Heatmap ────────────────────────────────────────────
    st.markdown("**Top Terms Heatmap**")
    try:
        terms_df = clusterer.get_top_terms_matrix(n_terms=8)
        fig, ax = plt.subplots(figsize=(12, max(6, len(terms_df) * 0.3)))
        sns.heatmap(
            terms_df, annot=True, fmt='.2f', cmap='YlOrRd', ax=ax,
            cbar_kws={'label': 'Term Importance Score'},
            linewidths=0.5, linecolor='gray',
        )
        ax.set_xlabel('Cluster', fontsize=11, fontweight='bold')
        ax.set_ylabel('Terms', fontsize=11, fontweight='bold')
        ax.set_title('Top Terms Importance by Cluster', fontsize=13, fontweight='bold')
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Heatmap error: {e}")

    st.divider()

    # ── Cluster Quality Metrics ──────────────────────────────────────
    st.markdown("**Cluster Quality Metrics**")
    m1, m2 = st.columns(2)
    with m1:
        inertia = clusterer.kmeans.inertia_
        st.metric("Inertia (Sum of Squared Distances)", f"{inertia:.2f}")
    with m2:
        avg_dist = np.sqrt(inertia / len(result_df))
        st.metric("Average Distance to Centroid", f"{avg_dist:.2f}")


if __name__ == "__main__":
    main()
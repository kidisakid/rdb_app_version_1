"""
Data Pipeline tool — cleaning, enrichment, and analysis on a single file.
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

from config import STEP_REGISTRY, GROUP_CONFIG
from src.cleaning.normalize_headers import normalize_headers
from src.cleaning.removing_duplicates import remove_duplicates
from src.cleaning.standardize_country import standardize_country
from src.cleaning.filter_values import filter_by_value
from src.transformation.add_dates_metadata import add_dates_metadata
from src.transformation.translate_columns import translate_columns
from src.clustering.topic_clustering import topic_cluster
from helpers import (
    get_group_color,
    load_uploaded_file, render_pipeline_strip, render_download,
)

PIPELINE_STEPS = [s for s in STEP_REGISTRY if s["group"] != "Merge"]


# ── Helpers for filter instances ─────────────────────────────────────

def _get_filter_instances() -> list[dict]:
    return st.session_state.get("pl_filter_instances", [])


def _set_filter_instances(instances: list[dict]):
    st.session_state["pl_filter_instances"] = instances


def _next_filter_id() -> str:
    counter = st.session_state.get("pl_filter_counter", 0) + 1
    st.session_state["pl_filter_counter"] = counter
    return f"filter_{counter}"


# ── Pipeline order management ────────────────────────────────────────

def _get_pipeline_order() -> list[str]:
    return st.session_state.get("pl_pipeline_order", [])


def _set_pipeline_order(order: list[str]):
    st.session_state["pl_pipeline_order"] = order


def _sync_pipeline_order(selected_labels: list[str], filter_instance_ids: list[str]):
    """Keep pipeline_order in sync: add new items, remove deselected ones."""
    order = _get_pipeline_order()
    valid_items = set(selected_labels) | set(filter_instance_ids)

    order = [item for item in order if item in valid_items]

    existing = set(order)
    for label in selected_labels:
        if label not in existing:
            order.append(label)
            existing.add(label)
    for fid in filter_instance_ids:
        if fid not in existing:
            order.append(fid)
            existing.add(fid)

    _set_pipeline_order(order)
    return order


def _resolve_order_to_labels(order: list[str]) -> list[str]:
    """Convert pipeline_order to step labels for execution and display."""
    instances = _get_filter_instances()
    id_to_num = {}
    for i, inst in enumerate(instances, 1):
        id_to_num[inst["instance_id"]] = i

    labels = []
    for item in order:
        if item.startswith("filter_"):
            num = id_to_num.get(item, "?")
            labels.append(f"Filter by column value #{num}")
        else:
            labels.append(item)
    return labels


# ── Sidebar ──────────────────────────────────────────────────────────

def render_pipeline_sidebar(col_names: list) -> tuple:

    # Uncheck filter checkbox if flagged by X button removal
    if st.session_state.pop("pl_uncheck_filter", False):
        st.session_state["filter_value"] = False

    groups: dict[str, list] = {}
    for step in PIPELINE_STEPS:
        groups.setdefault(step["group"], []).append(step)

    selected_labels = []

    # ── Step selection — flat grouped list ────────────────────────────
    for group_name, group_steps in groups.items():
        color = get_group_color(group_name)
        st.sidebar.markdown(
            f'<p style="font-family:DM Sans,sans-serif;font-size:0.68rem;font-weight:600;'
            f'color:{color};text-transform:uppercase;letter-spacing:0.1em;'
            f'margin:0.75rem 0 0.25rem 0;padding:0;">{group_name}</p>',
            unsafe_allow_html=True,
        )

        for step in group_steps:
            if step.get("repeatable"):
                checked = st.sidebar.checkbox(
                    step["label"],
                    key=step["id"],
                )
                # First check auto-creates an instance
                if checked and not _get_filter_instances():
                    new_id = _next_filter_id()
                    _set_filter_instances([{
                        "instance_id": new_id,
                        "column": None,
                        "values": [],
                    }])
                    st.rerun()
                # Unchecking removes all filter instances
                if not checked and _get_filter_instances():
                    _set_filter_instances([])
                    order = [o for o in _get_pipeline_order() if not o.startswith("filter_")]
                    _set_pipeline_order(order)
                    st.rerun()
            else:
                checked = st.sidebar.checkbox(
                    step["label"],
                    key=step["id"],
                    value=st.session_state.get(step["id"], False),
                )
                if checked:
                    selected_labels.append(step["label"])

    # Sync pipeline order
    filter_ids = [inst["instance_id"] for inst in _get_filter_instances()]
    order = _sync_pipeline_order(selected_labels, filter_ids)

    # Build the ordered step list for execution
    ordered_labels = _resolve_order_to_labels(order)

    # ── Per-step options (sidebar — non-filter steps only) ───────────
    has_options = any(
        label in selected_labels
        for label in ["Remove duplicates", "Standardize country", "Translate columns", "Topic clustering"]
    )

    dup_columns = None
    translate_cols_list = None
    target_lang = "en"
    source_lang = "auto"
    country_column = None
    convert_code = None
    cluster_params = None

    if has_options:
        st.sidebar.divider()
        st.sidebar.markdown(
            '<p style="font-family:DM Sans,sans-serif;font-size:0.68rem;font-weight:600;'
            'color:#94a3b8;text-transform:uppercase;letter-spacing:0.1em;'
            'margin:0 0 0.4rem 0;padding:0;">Options</p>',
            unsafe_allow_html=True,
        )

    if "Remove duplicates" in selected_labels:
        dup_columns = st.sidebar.multiselect(
            "Duplicate check columns",
            col_names,
            key="dup_cols",
            placeholder="Select columns...",
        )

    if "Standardize country" in selected_labels:
        country_column = st.sidebar.selectbox(
            "Country column",
            col_names,
            key="country_col",
            index=None,
            placeholder="Select column...",
        )
        convert_code = st.sidebar.selectbox(
            "Output format",
            ['ISO3', 'ISO2', 'name_short', 'name_official', 'continent', 'ISONumeric'],
            key="country_code",
        )

    if "Translate columns" in selected_labels:
        translate_cols_list = st.sidebar.multiselect(
            "Columns to translate",
            col_names,
            key="trans_cols",
            placeholder="Select columns...",
        )
        col1, col2 = st.sidebar.columns(2, gap="small")
        target_lang = col1.text_input("Target", value="en", key="target_lang")
        source_lang = col2.text_input("Source", value="auto", key="source_lang")

    if "Topic clustering" in selected_labels:
        cluster_text_col = st.sidebar.selectbox(
            "Text column",
            col_names,
            key="cluster_text_col",
            placeholder="Select column...",
        )
        col1, col2 = st.sidebar.columns(2, gap="small")
        cluster_n = col1.number_input(
            "Clusters", min_value=2, max_value=20, value=5, key="cluster_n"
        )
        cluster_n_init = col2.number_input(
            "K-Means inits", min_value=1, max_value=20, value=10, key="cluster_n_init"
        )
        col3, col4 = st.sidebar.columns(2, gap="small")
        cluster_max_df = col3.number_input(
            "Max DF", min_value=0.1, max_value=1.0, value=0.95, step=0.05, key="cluster_max_df"
        )
        cluster_min_df = col4.number_input(
            "Min DF", min_value=1, max_value=10, value=1, key="cluster_min_df"
        )
        cluster_clean = st.sidebar.checkbox("Clean text first", value=True, key="cluster_clean")
        cluster_params = {
            "text_column": cluster_text_col,
            "n_clusters": cluster_n,
            "max_df": cluster_max_df,
            "min_df": cluster_min_df,
            "n_init": cluster_n_init,
            "clean_text_option": cluster_clean,
        }

    return (ordered_labels, dup_columns, country_column, convert_code,
            translate_cols_list, target_lang, source_lang, cluster_params)


# ── Main page: filter configuration ─────────────────────────────────

def render_filter_section(input_df: pd.DataFrame) -> dict:
    """Render filter configuration on the main page. Returns filter_configs dict."""
    instances = _get_filter_instances()
    filter_configs = {}

    if not instances:
        return filter_configs

    filter_color = GROUP_CONFIG.get("Filter", {}).get("color", "#ec4899")

    st.markdown(
        '<div class="section-divider" style="margin-top:1.25rem">'
        '<span class="section-divider-label">Filters</span>'
        '<span class="section-divider-line"></span></div>',
        unsafe_allow_html=True,
    )

    col_names = list(input_df.columns)

    for i, inst in enumerate(instances, 1):
        iid = inst["instance_id"]

        st.markdown(
            f'<p style="font-family:DM Sans,sans-serif;font-size:0.75rem;'
            f'font-weight:600;color:{filter_color};margin:0 0 0.4rem 0;'
            f'text-transform:uppercase;letter-spacing:0.05em;">'
            f'Filter #{i}</p>',
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns([3, 5.5, 0.5])
        with c1:
            filter_col = st.selectbox(
                "Column",
                col_names,
                key=f"pl_filter_col_{iid}",
                index=None,
                placeholder="Select column...",
                label_visibility="collapsed",
            )
        with c2:
            filter_vals = []
            filter_range = None
            if filter_col and filter_col in input_df.columns:
                col_series = input_df[filter_col].dropna()
                is_numeric = pd.api.types.is_numeric_dtype(col_series)
                n_unique = col_series.nunique()

                if is_numeric and n_unique > 10:
                    # Numeric with many values — show range slider
                    col_min = float(col_series.min())
                    col_max = float(col_series.max())
                    filter_range = st.slider(
                        "Range",
                        min_value=col_min,
                        max_value=col_max,
                        value=(col_min, col_max),
                        key=f"pl_filter_range_{iid}",
                        label_visibility="collapsed",
                    )
                else:
                    # Categorical or few unique numeric values — show multiselect
                    unique_vals = sorted(
                        col_series.astype(str).unique().tolist()
                    )
                    filter_vals = st.multiselect(
                        "Values",
                        unique_vals,
                        key=f"pl_filter_vals_{iid}",
                        placeholder="Select values to keep...",
                        label_visibility="collapsed",
                    )
            else:
                st.markdown(
                    '<p style="font-size:0.8rem;color:#94a3b8;'
                    'padding:0.4rem 0;margin:0;">'
                    'Select a column first</p>',
                    unsafe_allow_html=True,
                )
        with c3:
            if st.button(
                "\u2715", key=f"pl_remove_{iid}",
                help="Remove this filter",
            ):
                new_instances = [x for x in instances if x["instance_id"] != iid]
                _set_filter_instances(new_instances)
                order = [o for o in _get_pipeline_order() if o != iid]
                _set_pipeline_order(order)
                if not new_instances:
                    st.session_state["pl_uncheck_filter"] = True
                st.rerun()

        filter_configs[iid] = {
            "column": filter_col,
            "values": filter_vals,
            "range": filter_range,
        }

    if st.button("+ Add another filter", key="pl_add_filter_main"):
        new_id = _next_filter_id()
        instances.append({
            "instance_id": new_id,
            "column": None,
            "values": [],
        })
        _set_filter_instances(instances)
        st.rerun()

    return filter_configs


# ── Pipeline runner ──────────────────────────────────────────────────

def run_cleaning_pipeline(
    temp_path: str,
    steps: list,
    dup_columns: list | None,
    country_column: str | None,
    convert_code: str | None,
    translate_columns_list: list | None,
    target_lang: str,
    source_lang: str,
    progress_placeholder,
    cluster_params: dict | None = None,
    filter_configs: dict | None = None,
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

            elif step == "Standardize country":
                if not country_column:
                    continue
                else:
                    df = standardize_country(
                        column=country_column,
                        file_path=temp_path,
                        convert_code=convert_code
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
                if hasattr(df, 'attrs') and 'clusterer' in df.attrs:
                    st.session_state['_clusterer'] = df.attrs['clusterer']
                    st.session_state['_cluster_text_col'] = df.attrs.get('cluster_text_column')
                    st.session_state['_cluster_n'] = params.get("n_clusters", 5)

            elif step.startswith("Filter by column value"):
                instance_id = _extract_filter_id(step)
                cfg = (filter_configs or {}).get(instance_id, {})
                col = cfg.get("column")
                vals = cfg.get("values", [])
                val_range = cfg.get("range")
                if col and val_range:
                    df = filter_by_value(
                        file_path=temp_path, column=col, value_range=val_range,
                    )
                elif col and vals:
                    df = filter_by_value(file_path=temp_path, column=col, values=vals)
                else:
                    st.warning(f"{step}: no column/values configured, skipping.")
                    continue

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


def _extract_filter_id(step_label: str) -> str:
    """Extract filter instance_id from a label like 'Filter by column value #2'."""
    instances = _get_filter_instances()
    try:
        num = int(step_label.split("#")[1]) - 1
        if 0 <= num < len(instances):
            return instances[num]["instance_id"]
    except (IndexError, ValueError):
        pass
    return ""


# ── Clustering visualizations ────────────────────────────────────────

def display_clustering_visualizations(result_df: pd.DataFrame):
    clusterer = st.session_state.get('_clusterer')
    text_column = st.session_state.get('_cluster_text_col')
    n_clusters = st.session_state.get('_cluster_n', 5)

    if clusterer is None or 'Cluster_Topic' not in result_df.columns:
        return

    st.markdown(
        '<div class="section-divider" style="margin-top:1.5rem">'
        '<span class="section-divider-label">Clustering Analysis</span>'
        '<span class="section-divider-line"></span></div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("**Cluster Distribution**")
        cluster_counts = result_df['Cluster_Topic'].value_counts().sort_index()
        st.dataframe(cluster_counts.rename('Count'), use_container_width=True)
    with col2:
        st.bar_chart(result_df['Cluster_Topic'].value_counts().sort_index())

    st.divider()

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

    st.markdown("**Cluster Quality Metrics**")
    m1, m2 = st.columns(2)
    with m1:
        inertia = clusterer.kmeans.inertia_
        st.metric("Inertia (Sum of Squared Distances)", f"{inertia:.2f}")
    with m2:
        avg_dist = np.sqrt(inertia / len(result_df))
        st.metric("Average Distance to Centroid", f"{avg_dist:.2f}")


# ── Main page ────────────────────────────────────────────────────────

def tool_data_pipeline():
    st.markdown("""
    <div class="page-hero">
        <div class="hero-eyebrow">Media Intelligence Platform</div>
        <p class="main-header">Data Pipeline</p>
        <p class="main-subtitle">Transform raw media data into clean, enriched datasets ready for analysis.</p>
        <div class="hero-actions">
            <span class="hero-badge"><span class="hero-badge-dot"></span>Ready</span>
            <span class="hero-badge">CSV &amp; Excel</span>
            <span class="hero-badge">7 operations</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── File upload (single) ─────────────────────────────────────────
    st.markdown(
        '<div class="section-divider">'
        '<span class="section-divider-label">Input</span>'
        '<span class="section-divider-line"></span></div>',
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
        key="pipeline_uploader",
    )

    if not uploaded_file:
        st.markdown("""
        <div style="font-family:'DM Sans',sans-serif;font-size:0.82rem;color:#94a3b8;
             text-align:center;padding:1rem 0;letter-spacing:0.01em;">
            Drop a file above to begin — supports CSV, XLSX, XLS up to 200MB
        </div>
        """, unsafe_allow_html=True)
        return

    # Reset state on new file
    file_id = uploaded_file.file_id
    if st.session_state.get("pl_last_file_id") != file_id:
        for key in [k for k in st.session_state.keys() if k.startswith("pl_")]:
            del st.session_state[key]
        st.session_state["pl_last_file_id"] = file_id

    try:
        input_df, _ = load_uploaded_file(uploaded_file)
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return

    col_names = list(input_df.columns)
    (selected_steps, dup_columns, country_column, convert_code,
     translate_cols_list, target_lang, source_lang,
     cluster_params) = render_pipeline_sidebar(col_names)

    # Clear results when pipeline steps change
    if selected_steps != st.session_state.get("pl_last_steps"):
        st.session_state.pop("result_df", None)
        st.session_state.pop("result_input_rows", None)
        st.session_state["pl_last_steps"] = list(selected_steps)

    # ── Metric cards ─────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider">'
        '<span class="section-divider-label">Dataset Overview</span>'
        '<span class="section-divider-line"></span></div>',
        unsafe_allow_html=True,
    )
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

    # ── Data preview ─────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider" style="margin-top:1.25rem">'
        '<span class="section-divider-label">Preview</span>'
        '<span class="section-divider-line"></span></div>',
        unsafe_allow_html=True,
    )
    st.dataframe(input_df.head(5), use_container_width=True, height=220)

    # ── Filters (main page) ──────────────────────────────────────────
    filter_configs = render_filter_section(input_df)

    # ── Pipeline strip + Run ─────────────────────────────────────────
    if selected_steps:
        render_pipeline_strip(selected_steps)

    st.markdown(
        '<div class="section-divider">'
        '<span class="section-divider-label">Execute</span>'
        '<span class="section-divider-line"></span></div>',
        unsafe_allow_html=True,
    )
    run_clicked = st.button(
        "Run Pipeline", type="primary",
        disabled=not selected_steps, use_container_width=False,
    )

    if not selected_steps:
        st.markdown(
            '<p style="font-family:DM Sans,sans-serif;font-size:0.78rem;'
            'color:#94a3b8;margin-top:0.25rem">'
            'Select at least one pipeline step from the sidebar to begin.</p>',
            unsafe_allow_html=True,
        )

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
            result_df = run_cleaning_pipeline(
                tmp_path, selected_steps, dup_columns, country_column, convert_code,
                translate_cols_list if "Translate columns" in selected_steps else None,
                target_lang, source_lang, progress_placeholder,
                cluster_params=cluster_params if "Topic clustering" in selected_steps else None,
                filter_configs=filter_configs,
            )
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except OSError:
                pass

        if result_df is not None:
            st.session_state["result_df"] = result_df
            st.session_state["result_input_rows"] = len(input_df)

    if "result_df" in st.session_state:
        result_df = st.session_state["result_df"]
        input_rows = st.session_state["result_input_rows"]

        # ── Results ──────────────────────────────────────────────────
        st.markdown(
            '<div class="section-divider" style="margin-top:1.5rem">'
            '<span class="section-divider-label">Results</span>'
            '<span class="section-divider-line"></span></div>',
            unsafe_allow_html=True,
        )

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
            delta = input_rows - len(result_df)
            sign = "\u2212" if delta > 0 else "+"
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

        # ── Download ─────────────────────────────────────────────────
        render_download(result_df, Path(uploaded_file.name).stem)

        # ── Topic Clustering Visualizations ──────────────────────────
        if "Topic clustering" in selected_steps and st.session_state.get('_clusterer'):
            display_clustering_visualizations(result_df)

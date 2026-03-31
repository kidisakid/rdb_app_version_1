"""
Shared helper functions used across tools.
"""

import io
from pathlib import Path

import pandas as pd
import streamlit as st

import config
from config import STEP_REGISTRY, GROUP_CONFIG


def get_group_color(group: str) -> str:
    return GROUP_CONFIG.get(group, {}).get("color", "#94a3b8")


def get_group_bg(group: str) -> str:
    return GROUP_CONFIG.get(group, {}).get("bg", "#f8fafc")


def detect_encoding(uploaded_file) -> str:
    raw = uploaded_file.read(50_000)
    uploaded_file.seek(0)
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return "utf-16"
    for enc in config.CSV_ENCODINGS:
        if enc == "utf-16":
            continue
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
        if encoding == "utf-16":
            text = uploaded_file.read().decode("utf-16")
            uploaded_file.seek(0)
            buf = io.BytesIO(text.encode("utf-8"))
            return pd.read_csv(buf, encoding="utf-8", sep="\t", on_bad_lines="skip"), encoding
        return (
            pd.read_csv(uploaded_file, encoding=encoding, on_bad_lines="skip"),
            encoding,
        )
    raise ValueError("Unsupported format. Use CSV or Excel (.xlsx, .xls).")


def render_pipeline_strip(selected_steps: list):
    if not selected_steps:
        return
    chips = []
    for i, label in enumerate(selected_steps):
        base_label = label.split(" #")[0] if " #" in label else label
        step = next((s for s in STEP_REGISTRY if s["label"] == base_label), None)
        group = step["group"] if step else "Cleaning"
        color = get_group_color(group)
        bg = get_group_bg(group)
        chips.append(
            f'<span class="pipeline-chip" style="background:{bg};color:{color};border:1px solid {color}44">'
            f'{label}</span>'
        )
        if i < len(selected_steps) - 1:
            chips.append('<span class="pipeline-arrow">\u2192</span>')

    st.markdown(
        '<div class="pipeline-strip"><span class="pipeline-label">Pipeline:</span>'
        + "".join(chips) + '</div>',
        unsafe_allow_html=True,
    )


def render_download(result_df: pd.DataFrame, default_name: str):
    st.markdown(
        '<div class="section-divider" style="margin-top:1rem">'
        '<span class="section-divider-label">Download</span>'
        '<span class="section-divider-line"></span></div>',
        unsafe_allow_html=True,
    )
    out_format = st.radio("Format", ["CSV", "Excel"], horizontal=True, key="out_fmt")

    if "output_base_name" not in st.session_state:
        st.session_state["output_base_name"] = default_name
    filename = st.text_input("Output filename: ", key="output_base_name")

    if out_format == "CSV":
        st.download_button(
            label="Download CSV",
            data=result_df.to_csv(index=False).encode("utf-8"),
            file_name=filename + "_cleaned.csv",
            mime="text/csv",
        )
    else:
        buf = io.BytesIO()
        result_df.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        st.download_button(
            label="Download Excel",
            data=buf.getvalue(),
            file_name=filename + "_cleaned.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

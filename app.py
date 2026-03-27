"""
RDB App — main entry point.
Handles page config, styles, and tool routing.
"""

import sys
import warnings
from pathlib import Path

import streamlit as st

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Page config
st.set_page_config(
    page_title="RDB App",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styles
from styles import STYLES
st.markdown(STYLES, unsafe_allow_html=True)

from tools import tool_data_pipeline, tool_merge_csv


# ── Tool selector ────────────────────────────────────────────────────

TOOLS = [
    {"id": "pipeline", "label": "Data Pipeline", "icon": ":material/tune:"},
    {"id": "merge", "label": "Merge Data", "icon": ":material/merge:"},
]

def _render_tool_selector():
    if "active_tool" not in st.session_state:
        st.session_state["active_tool"] = "pipeline"

    st.sidebar.markdown('<p class="sidebar-app-name">RDB App</p>', unsafe_allow_html=True)

    for t in TOOLS:
        is_active = st.session_state["active_tool"] == t["id"]
        active_cls = "active" if is_active else ""
        if st.sidebar.button(
            t["label"],
            key=f"tool_btn_{t['id']}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
            icon=t["icon"],
        ):
            if not is_active:
                st.session_state["active_tool"] = t["id"]
                st.rerun()
    st.sidebar.divider()
    return st.session_state["active_tool"]

# ── Main ─────────────────────────────────────────────────────────────

def main():
    active = _render_tool_selector()

    if active == "pipeline":
        tool_data_pipeline()
    else:
        tool_merge_csv()


if __name__ == "__main__":
    main()

"""
RDB App — main entry point.
Handles page config, styles, and role-based tool routing.
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

from tools import tool_data_pipeline, tool_merge_csv, tool_user_control
from auth import is_authenticated, is_admin, render_auth_page, render_sidebar_header


# ── Tool definitions ─────────────────────────────────────────────────

USER_TOOLS = [
    {"id": "pipeline", "label": "Data Pipeline", "icon": ":material/tune:"},
    {"id": "merge",    "label": "Merge Data",     "icon": ":material/merge:"},
]

ADMIN_TOOLS = USER_TOOLS + [
    {"id": "users",    "label": "User Control",   "icon": ":material/manage_accounts:"},
]


# ── Sidebar tool selector ────────────────────────────────────────────

def _render_tool_selector() -> str:
    tools = ADMIN_TOOLS if is_admin() else USER_TOOLS
    default = tools[0]["id"]

    if "active_tool" not in st.session_state:
        st.session_state["active_tool"] = default

    # Guard: reset if current tool not available for this role
    if st.session_state["active_tool"] not in {t["id"] for t in tools}:
        st.session_state["active_tool"] = default

    render_sidebar_header()

    for t in tools:
        is_active = st.session_state["active_tool"] == t["id"]
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
    if not is_authenticated():
        render_auth_page()
        return

    active = _render_tool_selector()

    if active == "pipeline":
        tool_data_pipeline()
    elif active == "merge":
        tool_merge_csv()
    elif active == "users" and is_admin():
        tool_user_control()
    else:
        st.error("You do not have permission to access this page.")


if __name__ == "__main__":
    main()

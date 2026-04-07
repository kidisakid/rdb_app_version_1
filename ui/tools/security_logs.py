"""
Security Logs tool — Admin-only read-only viewer for the `security_events`
MongoDB collection.

Shows the most recent login / change-password / admin-reset / lockout events,
with simple filters and a CSV download. Backend access is gated via
`auth.get_security_events` (which itself checks `is_admin()`), and the UI
refuses to render for non-admin sessions as defense in depth.
"""

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from auth import get_security_events, is_admin


# Canonical event labels the backend emits (keep in sync with auth/core.py).
_EVENT_OPTIONS = [
    "All",
    "login",
    "login_locked",
    "login_lockout",
    "change_password",
    "change_password_locked",
    "change_password_lockout",
    "admin_reset_password",
]


def _friendly_timestamp(ts) -> str:
    """Render a timestamp in the user's local timezone. Mongo may return naive
    datetimes for legacy records — treat those as UTC."""
    if not isinstance(ts, datetime):
        return ""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def tool_security_logs():
    # Defense in depth — the backend also checks is_admin().
    if not is_admin():
        st.error("You do not have permission to view security logs.")
        return

    st.markdown("""
    <div class="page-hero">
        <div class="hero-eyebrow">Admin Panel</div>
        <p class="main-header">Security Logs</p>
        <p class="main-subtitle">
            Read-only audit trail of logins, password changes, admin resets, and lockouts.
        </p>
        <div class="hero-actions">
            <span class="hero-badge"><span class="hero-badge-dot"></span>Admin only</span>
            <span class="hero-badge">Read-only</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Filters ──────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider">'
        '<span class="section-divider-label">Filters</span>'
        '<span class="section-divider-line"></span></div>',
        unsafe_allow_html=True,
    )

    col_event, col_user, col_fail, col_limit = st.columns([2, 2, 1, 1], vertical_alignment="bottom")
    with col_event:
        event_choice = st.selectbox("Event type", _EVENT_OPTIONS, index=0)
    with col_user:
        username_filter = st.text_input(
            "Username contains", placeholder="Leave blank for all users"
        )
    with col_fail:
        only_failures = st.toggle("Failures only", value=False)
    with col_limit:
        limit = st.number_input("Limit", min_value=10, max_value=1000, value=200, step=10)

    # ── Fetch ────────────────────────────────────────────────────────
    event_arg = None if event_choice == "All" else event_choice
    try:
        events = get_security_events(
            limit=int(limit),
            event=event_arg,
            username=username_filter.strip() or None,
            only_failures=only_failures,
        )
    except Exception as e:
        st.error(f"Failed to load security events: {e}")
        return

    st.markdown(
        '<div class="section-divider" style="margin-top:1.5rem">'
        '<span class="section-divider-label">Recent Events</span>'
        '<span class="section-divider-line"></span></div>',
        unsafe_allow_html=True,
    )

    if not events:
        st.info(
            "No security events match the current filters. "
            "If this is the first run after deploying the audit log, "
            "sign in once to generate a record."
        )
        return

    # ── Render ───────────────────────────────────────────────────────
    rows = [
        {
            "Timestamp": _friendly_timestamp(e.get("timestamp")),
            "Event": e.get("event", ""),
            "Username": e.get("username", ""),
            "Actor": e.get("actor", ""),
            "Status": "✅ success" if e.get("success") else "❌ failure",
        }
        for e in events
    ]
    df = pd.DataFrame(rows)

    # Summary chips
    total = len(df)
    failures = sum(1 for e in events if not e.get("success"))
    st.caption(
        f"Showing **{total}** most recent events · "
        f"**{failures}** failures · "
        f"**{total - failures}** successes"
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
            "Event":     st.column_config.TextColumn("Event",     width="medium"),
            "Username":  st.column_config.TextColumn("Username",  width="small"),
            "Actor":     st.column_config.TextColumn("Actor",     width="small"),
            "Status":    st.column_config.TextColumn("Status",    width="small"),
        },
    )

    st.download_button(
        "Download as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"security_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        icon=":material/download:",
    )

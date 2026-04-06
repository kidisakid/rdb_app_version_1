"""
CSS styles for the Data Pipeline app.
Import and inject via: st.markdown(STYLES, unsafe_allow_html=True)
"""

STYLES = """
<style>
/* ── Google Fonts ───────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Main page ─────────────────────────────────── */
.main-header {
    font-family: 'DM Serif Display', Georgia, serif;
    font-weight: 400;
    font-size: 2.2rem;
    color: #0f172a;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
    line-height: 1.15;
}
.main-subtitle {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    color: #64748b;
    font-weight: 400;
    margin-bottom: 0;
    letter-spacing: 0.01em;
}
.page-hero {
    padding: 1.8rem 2rem 1.5rem;
    background: linear-gradient(135deg, #f8faff 0%, #f0f4ff 50%, #faf8ff 100%);
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    margin-bottom: 1.75rem;
    position: relative;
    overflow: hidden;
}
.page-hero::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.page-hero::after {
    content: '';
    position: absolute;
    bottom: -30px; left: 30%;
    width: 150px; height: 150px;
    background: radial-gradient(circle, rgba(245,158,11,0.06) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-eyebrow {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.65rem;
    font-weight: 600;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    margin-bottom: 0.5rem;
}
.hero-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-top: 0.9rem;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.68rem;
    font-weight: 500;
    color: #475569;
    background: rgba(255, 255, 255, 0.65);
    border: 1px solid rgba(226, 232, 240, 0.9);
    border-radius: 20px;
    padding: 3px 10px;
    letter-spacing: 0.01em;
}
.hero-badge-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #22c55e;
    display: inline-block;
    flex-shrink: 0;
    box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.2);
}

.section-title {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.68rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin: 1.5rem 0 0.6rem;
}
.section-divider {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 1.5rem 0 0.8rem;
}
.section-divider-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.68rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    white-space: nowrap;
}
.section-divider-line {
    flex: 1;
    height: 1px;
    background: #e2e8f0;
}

/* ── Sidebar spacing ───────────────────────────── */
section[data-testid="stSidebar"] .stMarkdown { margin-bottom: 0 !important; }
section[data-testid="stSidebar"] .element-container { margin-bottom: 0 !important; }
section[data-testid="stSidebar"] .block-container { gap: 0 !important; }
section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] { gap: 0 !important; margin: 0 !important; padding: 0 !important; }
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.25rem !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-top: 1.5rem !important;
}
/* Collapse columns wrapper spacing */
section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] { gap: 0.5rem !important; margin: 0 !important; padding: 0 !important; }
section[data-testid="stSidebar"] [data-testid="column"] { padding: 0 !important; margin: 0 !important; }
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div { margin: 0 !important; padding: 0 !important; }

/* ── Sidebar divider compact ─────────────────── */
section[data-testid="stSidebar"] hr {
    margin-top: 0.75rem !important;
    margin-bottom: 1.5rem !important;
}

/* ── Sidebar checkboxes ────────────────────────── */
section[data-testid="stSidebar"] .stCheckbox {
    margin-bottom: -0.6rem !important;
}
section[data-testid="stSidebar"] .stCheckbox label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.8rem !important;
    color: #475569 !important;
    padding: 0.2rem 0 !important;
}
section[data-testid="stSidebar"] .stCheckbox label:hover { color: #1e293b !important; }

/* ── Sidebar select/multiselect compact ────────── */
section[data-testid="stSidebar"] .stSelectbox,
section[data-testid="stSidebar"] .stMultiSelect {
    margin-bottom: -0.4rem !important;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.72rem !important;
    color: #94a3b8 !important;
}
section[data-testid="stSidebar"] .stNumberInput {
    margin-bottom: -0.4rem !important;
}
section[data-testid="stSidebar"] .stNumberInput label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.72rem !important;
    color: #94a3b8 !important;
}


/* ── Pipeline strip ─────────────────────────────── */
.pipeline-strip {
    display: flex; flex-wrap: wrap; align-items: center; gap: 6px;
    background: #f8faff; border: 1px solid #e0e7ff;
    border-radius: 12px; padding: 10px 16px; margin-bottom: 1.25rem;
    font-family: 'DM Sans', sans-serif;
}
.pipeline-chip {
    font-size: 0.72rem; font-weight: 600;
    padding: 3px 11px; border-radius: 20px;
    letter-spacing: 0.01em;
}
.pipeline-arrow { color: #c7d2fe; font-size: 0.85rem; }
.pipeline-label { font-size: 0.68rem; color: #94a3b8; margin-right: 4px; font-weight: 500; letter-spacing: 0.06em; text-transform: uppercase; }

/* ── File uploader ──────────────────────────────── */
[data-testid="stFileUploader"] section {
    padding: 2.5rem 2rem !important;
    border-radius: 14px !important;
    border: 1.5px dashed #c7d2fe !important;
    background: linear-gradient(135deg, #f8faff, #f5f3ff) !important;
    transition: border-color 0.2s, background 0.2s !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: #818cf8 !important;
    background: linear-gradient(135deg, #eef2ff, #f0f4ff) !important;
}

/* ── Metric cards ───────────────────────────────── */
.status-box {
    background: #ffffff; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 1.1rem 1.25rem 1rem;
    position: relative; overflow: hidden; transition: box-shadow .2s, border-color .2s;
}
.status-box:hover { border-color: #cbd5e1; box-shadow: 0 4px 16px rgba(26,26,46,.07); }
.status-box::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; border-radius: 10px 10px 0 0;
}
.status-box.rows::before { background: #6366f1; }
.status-box.cols::before { background: #f59e0b; }
.status-box.countries::before { background: #8b5cf6; }
.status-icon { font-size: .72rem; color: #94a3b8; text-transform: uppercase; letter-spacing: .08em; font-weight: 600; margin-bottom: .35rem; }
.status-val  { font-size: 1.75rem; font-weight: 700; line-height: 1; color: #1a1a2e; letter-spacing: -.02em; margin-bottom: .3rem; }
.status-lbl  { font-size: .78rem; color: #64748b; font-weight: 500; }

/* ── Dark mode ──────────────────────────────────── */
@media (prefers-color-scheme: dark) {

    /* ── Main page ── */
    .main-header { color: #f1f5f9; }
    .main-subtitle { color: #94a3b8; }

    /* Hero banner */
    .page-hero {
        background: linear-gradient(135deg, #13152a 0%, #1a1d35 50%, #16132a 100%);
        border-color: #2d3158;
    }
    .page-hero::before {
        background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
    }
    .page-hero::after {
        background: radial-gradient(circle, rgba(245,158,11,0.1) 0%, transparent 70%);
    }
    .hero-eyebrow { color: #818cf8; }
    .hero-badge {
        background: #1e2235;
        border-color: #2d3158;
        color: #94a3b8;
    }
    .hero-badge-dot {
        box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.12);
    }

    /* Section dividers */
    .section-divider-label { color: #475569; }
    .section-divider-line { background: #1e2235; }

    /* Metric cards */
    .status-box {
        background: #13152a;
        border-color: #1e2235;
    }
    .status-box:hover {
        border-color: #3730a3;
        box-shadow: 0 8px 28px rgba(99,102,241,0.15);
        transform: translateY(-2px);
    }
    .status-box.rows::before { background: linear-gradient(90deg,#4f46e5,#6366f1); }
    .status-box.cols::before { background: linear-gradient(90deg,#d97706,#f59e0b); }
    .status-box.countries::before { background: linear-gradient(90deg,#7c3aed,#8b5cf6); }
    .status-val { color: #f1f5f9; }
    .status-icon { color: #475569; }
    .status-lbl { color: #64748b; }

    /* Pipeline strip */
    .pipeline-strip {
        background: #13152a;
        border-color: #1e2235;
    }
    .pipeline-label { color: #475569; }
    .pipeline-arrow { color: #2d3158; }

    /* File uploader */
    [data-testid="stFileUploader"] section {
        background: linear-gradient(135deg, #13152a, #16132a) !important;
        border-color: #2d3158 !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: #4f46e5 !important;
        background: linear-gradient(135deg, #1a1d35, #1e1a35) !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] .stCheckbox label { color: #94a3b8 !important; }
    section[data-testid="stSidebar"] .stCheckbox label:hover { color: #e2e8f0 !important; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label,
    section[data-testid="stSidebar"] .stNumberInput label { color: #64748b !important; }


}

/* ── Auth page ──────────────────────────────────── */
.auth-card {
    text-align: center;
    padding: 2.75rem 0 1.75rem;
}
.auth-logo {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.1rem;
    font-weight: 400;
    letter-spacing: 0.08em;
    color: #ffffff;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    width: 52px;
    height: 52px;
    border-radius: 14px;
    margin: 0 auto 1rem;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}
.auth-eyebrow {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.65rem;
    font-weight: 600;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    margin-bottom: 0.5rem;
}
.auth-title {
    font-family: 'DM Serif Display', Georgia, serif !important;
    font-size: 3.2rem !important;
    font-weight: 400 !important;
    color: #0f172a;
    letter-spacing: -0.02em !important;
    margin: 0 0 0.4rem !important;
    line-height: 1.1 !important;
}
.auth-subtitle {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    color: #94a3b8;
    margin: 0 0 0;
}

/* ── Auth tabs — segmented control ─────────────── */
[class*="st-key-auth_tabs_wrapper"] .stTabs [data-baseweb="tab-list"] {
    background: #f1f5f9;
    border-radius: 12px;
    padding: 4px;
    gap: 2px;
    border: 1px solid #e2e8f0;
    margin-bottom: 0.25rem;
}
[class*="st-key-auth_tabs_wrapper"] .stTabs [data-baseweb="tab"] {
    border-radius: 9px;
    padding: 8px 0;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    font-weight: 500;
    color: #64748b;
    background: transparent;
    flex: 1;
    justify-content: center;
    transition: color 0.15s ease, background 0.15s ease;
}
[class*="st-key-auth_tabs_wrapper"] .stTabs [data-baseweb="tab"]:hover {
    color: #1e293b;
}
[class*="st-key-auth_tabs_wrapper"] .stTabs [aria-selected="true"] {
    background: #ffffff;
    color: #1e293b;
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 0 0 0.5px rgba(0, 0, 0, 0.04);
}
[class*="st-key-auth_tabs_wrapper"] .stTabs [data-baseweb="tab-highlight"],
[class*="st-key-auth_tabs_wrapper"] .stTabs [data-baseweb="tab-border"] {
    display: none !important;
}
[class*="st-key-auth_tabs_wrapper"] .stTabs [data-baseweb="tab-panel"] {
    padding: 1.25rem 0 0 !important;
}

@media (prefers-color-scheme: dark) {
    .auth-title    { color: #f1f5f9; }
    .auth-subtitle { color: #475569; }
    .auth-eyebrow  { color: #818cf8; }
    .auth-logo     { box-shadow: 0 4px 20px rgba(99, 102, 241, 0.45); }
    [class*="st-key-auth_tabs_wrapper"] .stTabs [data-baseweb="tab-list"] {
        background: rgba(15, 17, 23, 0.8);
        border-color: #1e2235;
    }
    [class*="st-key-auth_tabs_wrapper"] .stTabs [data-baseweb="tab"] {
        color: #475569;
    }
    [class*="st-key-auth_tabs_wrapper"] .stTabs [data-baseweb="tab"]:hover {
        color: #94a3b8;
    }
    [class*="st-key-auth_tabs_wrapper"] .stTabs [aria-selected="true"] {
        background: #1e2235;
        color: #e2e8f0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    }
}

/* ── Sidebar header (title + username) ─────────── */
.sidebar-app-name {
    font-family: 'DM Serif Display', Georgia, serif !important;
    font-size: 1.5rem !important;
    font-weight: 400 !important;
    letter-spacing: -0.01em !important;
    text-align: left !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.3 !important;
}
.sidebar-username {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    font-weight: 400;
    margin: 0 !important;
    margin-top: 0.25rem !important;
    padding: 0;
}
.sidebar-user-row {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 0 !important;
    padding: 0;
}

/* ── Role badges ────────────────────────────────── */
.role-badge {
    display: inline-flex;
    align-items: center;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.6rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 2px 7px;
    border-radius: 20px;
    line-height: 1.4;
}
.role-super {
    background: rgba(245, 158, 11, 0.12);
    color: #92400e;
    border: 1px solid rgba(245, 158, 11, 0.3);
}
.role-admin {
    background: rgba(99, 102, 241, 0.12);
    color: #4338ca;
    border: 1px solid rgba(99, 102, 241, 0.25);
}
.role-user {
    background: rgba(100, 116, 139, 0.1);
    color: #64748b;
    border: 1px solid rgba(100, 116, 139, 0.2);
}
@media (prefers-color-scheme: dark) {
    .role-super {
        background: rgba(251, 191, 36, 0.12);
        color: #fbbf24;
        border-color: rgba(251, 191, 36, 0.25);
    }
    .role-admin {
        background: rgba(129, 140, 248, 0.15);
        color: #a5b4fc;
        border-color: rgba(129, 140, 248, 0.3);
    }
    .role-user {
        background: rgba(148, 163, 184, 0.1);
        color: #94a3b8;
        border-color: rgba(148, 163, 184, 0.2);
    }
}

/* ── User Control — centered layout ────────────── */
.block-container:has(.uc-page-wrap) {
    max-width: 720px !important;
    margin: 0 auto !important;
}

/* ── User Control panel ─────────────────────────── */
.uc-header {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #94a3b8;
    padding-bottom: 0.35rem;
}
.uc-divider {
    height: 1px;
    background: #e2e8f0;
    margin: 0.25rem 0;
}
.uc-username {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    font-weight: 600;
    color: #1e293b;
}
.uc-handle {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.75rem;
    color: #94a3b8;
    font-weight: 400;
}
.uc-you {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.62rem;
    font-weight: 400;
    color: #94a3b8;
    background: rgba(148,163,184,0.12);
    padding: 1px 5px;
    border-radius: 4px;
    margin-left: 4px;
}

/* ── Promote button — green ─────────────────────── */
[class*="st-key-promote_"] button {
    color: #10b981 !important;
    background: rgba(16, 185, 129, 0.06) !important;
    border: 1px solid rgba(16, 185, 129, 0.2) !important;
    border-radius: 6px !important;
    min-width: 36px !important;
}
[class*="st-key-promote_"] button:hover {
    background: rgba(16, 185, 129, 0.14) !important;
    border-color: rgba(16, 185, 129, 0.4) !important;
}

/* ── Demote button — amber ──────────────────────── */
[class*="st-key-demote_"] button {
    color: #f59e0b !important;
    background: rgba(245, 158, 11, 0.06) !important;
    border: 1px solid rgba(245, 158, 11, 0.2) !important;
    border-radius: 6px !important;
    min-width: 36px !important;
}
[class*="st-key-demote_"] button:hover {
    background: rgba(245, 158, 11, 0.14) !important;
    border-color: rgba(245, 158, 11, 0.4) !important;
}

@media (prefers-color-scheme: dark) {
    [class*="st-key-promote_"] button {
        color: #34d399 !important;
        background: rgba(16, 185, 129, 0.08) !important;
        border-color: rgba(16, 185, 129, 0.25) !important;
    }
    [class*="st-key-promote_"] button:hover {
        background: rgba(16, 185, 129, 0.18) !important;
        border-color: rgba(16, 185, 129, 0.45) !important;
    }
    [class*="st-key-demote_"] button {
        color: #fbbf24 !important;
        background: rgba(245, 158, 11, 0.08) !important;
        border-color: rgba(245, 158, 11, 0.25) !important;
    }
    [class*="st-key-demote_"] button:hover {
        background: rgba(245, 158, 11, 0.18) !important;
        border-color: rgba(245, 158, 11, 0.45) !important;
    }
}

/* Compact row spacing in user list */
.st-key-sidebar_header ~ div [data-testid="stHorizontalBlock"],
[data-testid="stVerticalBlock"] [data-testid="stHorizontalBlock"]:has(.uc-username) {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}

/* ── User Control table header row ─────────────── */
.uc-table-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 0 0.35rem 0;
}
.uc-row-info {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 2px;
    padding: 0.2rem 0;
    line-height: 1.4;
}

/* User list action buttons — compact in column layout */
[class*="st-key-promote_"] button,
[class*="st-key-demote_"] button,
[class*="st-key-delete_"] button {
    padding: 0.3rem 0.5rem !important;
    min-height: 2rem !important;
    font-size: 0.8rem !important;
}
[class*="st-key-promote_"] button [data-testid="stIconMaterial"],
[class*="st-key-demote_"] button [data-testid="stIconMaterial"],
[class*="st-key-delete_"] button [data-testid="stIconMaterial"] {
    font-size: 1.1rem !important;
}

/* Delete button — red icon */
[data-testid*="delete_"] button,
[class*="st-key-delete_"] button {
    color: #ef4444 !important;
    background: rgba(239, 68, 68, 0.06) !important;
    border: 1px solid rgba(239, 68, 68, 0.2) !important;
    border-radius: 6px !important;
}
[data-testid*="delete_"] button:hover,
[class*="st-key-delete_"] button:hover {
    background: rgba(239, 68, 68, 0.14) !important;
    border-color: rgba(239, 68, 68, 0.4) !important;
}
@media (prefers-color-scheme: dark) {
    .uc-username { color: #e2e8f0; }
    .uc-handle   { color: #475569; }
    .uc-divider  { background: #1e2235; }
    .uc-you      { background: rgba(148,163,184,0.08); }
    [data-testid*="delete_"] button,
    [class*="st-key-delete_"] button {
        color: #f87171 !important;
        background: rgba(239, 68, 68, 0.08) !important;
        border-color: rgba(239, 68, 68, 0.25) !important;
    }
}

/* ── Sidebar header container — tight layout ──────── */
.st-key-sidebar_header {
    margin: 0 !important;
    padding: 0 !important;
    margin-bottom: 1.5rem !important;
}
.st-key-sidebar_header [data-testid="stVerticalBlock"] {
    gap: 0 !important;
}
.st-key-sidebar_header .element-container {
    margin: 0 !important;
}

/* Logout button wrapper — fixed to top-right of sidebar content */
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    position: relative !important;
}
.st-key-sidebar_header .st-key-logout_btn {
    position: absolute !important;
    top: 6rem !important;
    right: 0.3rem !important;
    width: 36px !important;
    height: 36px !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
}
.st-key-sidebar_header .st-key-logout_btn .stButton {
    width: 36px !important;
    height: 36px !important;
}

/* ── Logout button — high specificity to override generic sidebar btn */
section[data-testid="stSidebar"] .st-key-sidebar_header .stButton > button,
section[data-testid="stSidebar"] .st-key-sidebar_header .stButton > button[data-testid],
section[data-testid="stSidebar"] .st-key-sidebar_header button {
    all: unset !important;
    display: inline-flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0 !important;
    width: 36px !important;
    height: 36px !important;
    min-height: 36px !important;
    min-width: 36px !important;
    max-width: 36px !important;
    padding: 0 !important;
    border-radius: 8px !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    color: #94a3b8 !important;
    cursor: pointer !important;
    overflow: hidden !important;
    white-space: nowrap !important;
    transition: max-width 0.3s cubic-bezier(0.4,0,0.2,1),
                width 0.3s cubic-bezier(0.4,0,0.2,1),
                gap 0.3s cubic-bezier(0.4,0,0.2,1),
                padding 0.3s cubic-bezier(0.4,0,0.2,1),
                background 0.2s ease,
                border-color 0.2s ease,
                color 0.2s ease !important;
    margin: 0 !important;
    box-sizing: border-box !important;
}

/* "Logout" text — completely hidden */
section[data-testid="stSidebar"] .st-key-sidebar_header .stButton > button p,
section[data-testid="stSidebar"] .st-key-sidebar_header button p {
    display: none !important;
}
/* Center the icon span */
section[data-testid="stSidebar"] .st-key-sidebar_header .stButton > button span,
section[data-testid="stSidebar"] .st-key-sidebar_header button span {
    margin: 0 !important;
    padding: 0 !important;
    font-size: 1.4rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Hover — icon color change only */
section[data-testid="stSidebar"] .st-key-sidebar_header .stButton > button:hover,
section[data-testid="stSidebar"] .st-key-sidebar_header button:hover {
    background: transparent !important;
    border-color: transparent !important;
    color: #ef4444 !important;
}
section[data-testid="stSidebar"] .st-key-sidebar_header button:hover p {
    display: none !important;
    color: #ef4444 !important;
}

/* ── Light mode ───────────────────────────────────── */
@media (prefers-color-scheme: light) {
    .sidebar-app-name { color: #0f172a !important; }
    .sidebar-username { color: #94a3b8 !important; }
    .st-key-sidebar_header button { color: #94a3b8 !important; }
    .st-key-sidebar_header button:hover { color: #ef4444 !important; }
    .st-key-sidebar_header button:hover p { color: #ef4444 !important; }
}

/* ── Dark mode ────────────────────────────────────── */
@media (prefers-color-scheme: dark) {
    .sidebar-app-name { color: #f1f5f9 !important; }
    .sidebar-username { color: #64748b !important; }
    .st-key-sidebar_header button { color: #64748b !important; }
    .st-key-sidebar_header button:hover {
        background: rgba(239, 68, 68, 0.12) !important;
        border-color: rgba(239, 68, 68, 0.25) !important;
        color: #f87171 !important;
        justify-content: flex-start !important;
    }
    .st-key-sidebar_header button:hover p { color: #f87171 !important; }
}

/* ── Tool selector buttons (sidebar) ───────────── */
section[data-testid="stSidebar"] .stButton > button,
section[data-testid="stSidebar"] .stButton > button[data-testid] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 10px 14px !important;
    border-radius: 10px !important;
    transition: all 0.15s ease !important;
    letter-spacing: 0.01em !important;
    text-align: left !important;
    justify-content: flex-start !important;
    margin-bottom: 0.15rem;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
}
section[data-testid="stSidebar"] .stButton:not(.st-key-logout_btn) > button p,
section[data-testid="stSidebar"] .stButton:not(.st-key-logout_btn) > button span,
section[data-testid="stSidebar"] .stButton:not(.st-key-logout_btn) > button div,
section[data-testid="stSidebar"] .stButton:not(.st-key-logout_btn) > button * {
    text-align: left !important;
    justify-content: flex-start !important;
    margin-left: 0 !important;
    margin-right: auto !important;
}
section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background: transparent !important;
    border: none !important;
    color: #64748b !important;
}
section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
    background: rgba(99, 102, 241, 0.08) !important;
    color: #4338ca !important;
}
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
    background: rgba(99, 102, 241, 0.12) !important;
    border: none !important;
    color: #4338ca !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover {
    background: rgba(99, 102, 241, 0.18) !important;
}

@media (prefers-color-scheme: dark) {
    section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
        background: transparent !important;
        border: none !important;
        color: #94a3b8 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
        background: rgba(129, 140, 248, 0.1) !important;
        color: #a5b4fc !important;
    }
    section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
        background: rgba(129, 140, 248, 0.15) !important;
        border: none !important;
        color: #a5b4fc !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover {
        background: rgba(129, 140, 248, 0.22) !important;
    }
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; box-shadow: none !important; }
[data-testid="InputInstructions"] { display: none !important; }

/* ══════════════════════════════════════════════════
   RESPONSIVE BREAKPOINTS
   ══════════════════════════════════════════════════ */

/* ── Tablet (≤ 1024px) ──────────────────────────── */
@media (max-width: 1024px) {
    .block-container {
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    .page-hero {
        padding: 1.4rem 1.5rem 1.2rem !important;
    }
    .main-header {
        font-size: 1.9rem !important;
    }
    .status-val {
        font-size: 1.5rem !important;
    }
}

/* ── Mobile (≤ 768px) ───────────────────────────── */
@media (max-width: 768px) {
    /* Layout */
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1rem !important;
    }

    /* Hero */
    .page-hero {
        padding: 1.2rem 1.25rem 1rem !important;
        border-radius: 12px !important;
        margin-bottom: 1.25rem !important;
    }
    .main-header {
        font-size: 1.6rem !important;
        letter-spacing: -0.01em !important;
    }
    .main-subtitle {
        font-size: 0.82rem !important;
    }
    .hero-eyebrow {
        font-size: 0.6rem !important;
    }
    .hero-actions {
        flex-wrap: wrap !important;
        gap: 6px !important;
        margin-top: 0.75rem !important;
    }

    /* Section dividers */
    .section-divider {
        margin: 1rem 0 0.6rem !important;
    }

    /* Pipeline strip */
    .pipeline-strip {
        padding: 8px 12px !important;
        gap: 4px !important;
        border-radius: 10px !important;
    }
    .pipeline-chip {
        font-size: 0.68rem !important;
        padding: 2px 8px !important;
    }

    /* File uploader */
    [data-testid="stFileUploader"] section {
        padding: 1.75rem 1.25rem !important;
    }

    /* Metric cards */
    .status-box {
        padding: 0.9rem 1rem 0.85rem !important;
        border-radius: 8px !important;
    }
    .status-val {
        font-size: 1.4rem !important;
    }
    .status-lbl {
        font-size: 0.72rem !important;
    }

    /* Stack Streamlit columns vertically (general) */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        min-width: 100% !important;
        flex: 1 1 100% !important;
    }


    /* Auth page — expand center form column to full width */
    .auth-outer-col [data-testid="column"]:first-child,
    .auth-outer-col [data-testid="column"]:last-child {
        display: none !important;
    }
    .auth-outer-col [data-testid="column"]:nth-child(2) {
        min-width: 100% !important;
        flex: 1 1 100% !important;
    }

    /* User control — compact text on mobile */
    .uc-username { font-size: 0.78rem !important; }
    .uc-handle   { font-size: 0.68rem !important; }
    .uc-header   { font-size: 0.58rem !important; }
    .role-badge  { font-size: 0.55rem !important; padding: 1px 5px !important; }
    .uc-table-header { display: none !important; }

    /* Action buttons — smaller on tablet */
    [class*="st-key-promote_"] button,
    [class*="st-key-demote_"] button,
    [class*="st-key-delete_"] button {
        padding: 0.25rem 0.4rem !important;
        min-height: 1.8rem !important;
    }

    /* Sidebar */
    .sidebar-app-name {
        font-size: 1.1rem !important;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        font-size: 0.75rem !important;
    }
}

/* ── Small mobile (≤ 480px) ─────────────────────── */
@media (max-width: 480px) {
    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }
    .page-hero {
        padding: 1rem !important;
        border-radius: 10px !important;
    }
    .main-header {
        font-size: 1.4rem !important;
    }
    .main-subtitle {
        font-size: 0.78rem !important;
    }
    .status-val {
        font-size: 1.25rem !important;
    }
    .status-icon {
        font-size: 0.65rem !important;
    }
    [data-testid="stFileUploader"] section {
        padding: 1.25rem 1rem !important;
    }
    .pipeline-strip {
        padding: 6px 10px !important;
    }
    .pipeline-chip {
        font-size: 0.65rem !important;
        padding: 2px 6px !important;
    }
    [data-testid="stDownloadButton"] button {
        width: 100% !important;
    }

    /* Auth page — full-width form on tiny screens */
    [data-testid="stHorizontalBlock"]:has(.auth-form-col) > [data-testid="column"]:first-child,
    [data-testid="stHorizontalBlock"]:has(.auth-form-col) > [data-testid="column"]:last-child {
        display: none !important;
    }

    /* User control — tighten further on small screens */
    .uc-username { font-size: 0.72rem !important; }
    .uc-handle   { display: none !important; }
    .role-badge  { font-size: 0.52rem !important; padding: 1px 4px !important; }

    /* Action buttons — minimal on small mobile */
    [class*="st-key-promote_"] button,
    [class*="st-key-demote_"] button,
    [class*="st-key-delete_"] button {
        padding: 0.2rem 0.3rem !important;
        min-height: 1.6rem !important;
    }
    [class*="st-key-promote_"] button [data-testid="stIconMaterial"],
    [class*="st-key-demote_"] button [data-testid="stIconMaterial"],
    [class*="st-key-delete_"] button [data-testid="stIconMaterial"] {
        font-size: 0.95rem !important;
    }
}

/* ── Pipeline sidebar — options spacing ─────────── */
section[data-testid="stSidebar"] .stNumberInput {
    margin-bottom: 0.6rem !important;
}
section[data-testid="stSidebar"] .stSelectbox,
section[data-testid="stSidebar"] .stMultiSelect {
    margin-bottom: 0.6rem !important;
}

/* ── Pipeline sidebar — checkbox spacing ───────── */
section[data-testid="stSidebar"] .stCheckbox {
    margin-bottom: 0.2rem !important;
}
section[data-testid="stSidebar"] .stCheckbox label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 400 !important;
}
</style>
"""
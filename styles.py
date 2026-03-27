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

/* ── Sidebar divider compact ─────────────────── */
section[data-testid="stSidebar"] hr {
    margin-top: 0.3rem !important;
    margin-bottom: 0.3rem !important;
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

/* ── Sidebar app name ──────────────────────────── */
.sidebar-app-name {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.25rem;
    font-weight: 400;
    color: #0f172a;
    letter-spacing: -0.01em;
    text-align: left;
    margin: 0 0 1rem 0;
    padding: 0;
}
@media (prefers-color-scheme: dark) {
    .sidebar-app-name { color: #f1f5f9; }
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
    margin-bottom: -0.5rem;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
}
section[data-testid="stSidebar"] .stButton > button p,
section[data-testid="stSidebar"] .stButton > button span,
section[data-testid="stSidebar"] .stButton > button div,
section[data-testid="stSidebar"] .stButton > button * {
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
</style>
"""
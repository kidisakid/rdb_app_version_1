"""
Configuration file for the RDB application.
Contains file paths, settings, and other configuration constants.
"""

import sys
from pathlib import Path

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

_utils_dir = Path(__file__).parent / "src" / "utils"
if str(_utils_dir) not in sys.path:
    sys.path.insert(0, str(_utils_dir))

PROJECT_ROOT = Path(__file__).parent

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DATA_DIR = DATA_DIR / "output"
RAW_DATA_DIR = DATA_DIR / "raw"

RAW_DATA_FILE = RAW_DATA_DIR / "test.csv"

CSV_ENCODINGS = ['utf-8', 'utf-8-sig', 'utf-16', 'latin1', 'cp1252']
CSV_DELIMITERS = ['\t', ',', ';']

for directory in [DATA_DIR, OUTPUT_DATA_DIR, RAW_DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Add Steps
# To add a new step: append one dict
# Optional "min_files" key (default 1): minimum uploaded files needed to enable the step.
# Steps with min_files > 1 are automatically disabled when fewer files are uploaded.
STEP_REGISTRY = [
    {"id": "normalize",
     "group": "Cleaning",
     "label": "Normalize headers"},

    {"id": "duplicates",
     "group": "Cleaning",
     "label": "Remove duplicates"},

    {"id": "date",
     "group": "Enrichment",
     "label": "Add date metadata"},

    {"id": "translate",
     "group": "Enrichment",
     "label": "Translate columns"},

    {"id": "topic_cluster",
     "group": "Analysis",
     "label": "Topic clustering"},

    {"id": "merge_csv",
     "group": "Merge",
     "label": "Merge CSV files",
     "min_files": 2},
]

ALL_LABELS = [s["label"] for s in STEP_REGISTRY]

# Step Category Color — light mode
GROUP_CONFIG = {
    "Cleaning": {"color": "#6366f1", "bg": "#eef2ff"},
    "Enrichment": {"color": "#f59e0b", "bg": "#fffbeb"},
    "Transformation": {"color": "#10b981", "bg": "#ecfdf5"},
    "Analysis": {"color": "#0ea5e9", "bg": "#f0f9ff"},
    "Merge": {"color": "#8b5cf6", "bg": "#f5f3ff"},
}

# Step Category Color — dark mode
# Deep saturated bg so icons are visible on dark sidebar,
# lighter color so SVG strokes remain crisp against the dark bg.
GROUP_DARK_BG = {
    "Cleaning":"#1e1b4b",   # deep indigo
    "Enrichment":"#1c1710",   # deep amber
    "Transformation":"#052e1c",   # deep emerald
    "Analysis":"#0c2a3d",          # deep sky blue
    "Merge":"#2e1065",              # deep violet
}
GROUP_DARK_COLOR = {
    "Cleaning":"#818cf8",   # light indigo
    "Enrichment":"#fbbf24",   # light amber
    "Transformation":"#34d399",   # light emerald
    "Analysis":"#38bdf8",          # light sky blue
    "Merge":"#a78bfa",              # light violet
}
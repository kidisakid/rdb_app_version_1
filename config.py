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

CSV_ENCODINGS = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
CSV_DELIMITERS = ['\t', ',', ';']

for directory in [DATA_DIR, OUTPUT_DATA_DIR, RAW_DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Add Steps
# To add a new step: append one dict
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
]

ALL_LABELS = [s["label"] for s in STEP_REGISTRY]

# Step Category Color — light mode
GROUP_CONFIG = {
    "Cleaning": {"color": "#6366f1", "bg": "#eef2ff"},
    "Enrichment": {"color": "#f59e0b", "bg": "#fffbeb"},
    "Transformation": {"color": "#10b981", "bg": "#ecfdf5"},
}

# Step Category Color — dark mode
# Deep saturated bg so icons are visible on dark sidebar,
# lighter color so SVG strokes remain crisp against the dark bg.
GROUP_DARK_BG = {
    "Cleaning":"#1e1b4b",   # deep indigo
    "Enrichment":"#1c1710",   # deep amber
    "Transformation":"#052e1c",   # deep emerald
}
GROUP_DARK_COLOR = {
    "Cleaning":"#818cf8",   # light indigo
    "Enrichment":"#fbbf24",   # light amber
    "Transformation":"#34d399",   # light emerald
}
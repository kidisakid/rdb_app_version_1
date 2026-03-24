"""
Main src package - sets up all paths for the project.
"""
import sys
from pathlib import Path

_src_dir = Path(__file__).parent

if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from utils.csv_handler import read_csv, write_csv, append_csv, read_csv_to_dict
from cleaning.normalize_headers import normalize_headers
from cleaning.removing_duplicates import remove_duplicates
from transformation.add_dates_metadata import add_dates_metadata
from transformation.translate_columns import translate_columns
from clustering.topic_clustering import topic_cluster
from merge.merge_csv import merge_csv

__all__ = [
    'read_csv', 'write_csv', 'append_csv', 'read_csv_to_dict',
    'normalize_headers', 'remove_duplicates', 'add_dates_metadata',
    'translate_columns', 'topic_cluster', 'merge_csv'
]

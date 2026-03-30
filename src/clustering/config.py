"""Configuration and constants for the clustering module."""

# Default parameters for TopicClusterer
DEFAULT_N_CLUSTERS = 5
DEFAULT_MAX_DF = 0.95
DEFAULT_MIN_DF = 1
DEFAULT_RANDOM_STATE = 42
DEFAULT_N_INIT = 10

# TF-IDF Vectorizer configuration
TFIDF_MAX_FEATURES = 500
TFIDF_STOP_WORDS = 'english'

# Default output column name for clustering results
DEFAULT_OUTPUT_COLUMN = 'Cluster_Topic'

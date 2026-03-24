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

# K-Means configuration
KMEANS_ALGORITHM = 'lloyd'

# Text cleaning configuration
REMOVE_PUNCTUATION = True
REMOVE_NUMBERS = False
MIN_TOKEN_LENGTH = 3

# Custom stopwords (can be extended)
CUSTOM_STOPWORDS = set()

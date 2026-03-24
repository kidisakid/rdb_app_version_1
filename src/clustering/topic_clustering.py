"""
Topic Clustering using Cosine Similarity and K-Means.

This module provides functionality for clustering text data into topics
using TF-IDF vectorization, cosine similarity, and k-means clustering.
Adapted for integration into the RDB data pipeline.
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
import warnings
import re
import string

import config
from csv_handler import read_csv

warnings.filterwarnings('ignore')


def clean_text(text: str, remove_punctuation: bool = True, remove_numbers: bool = False) -> str:
    """
    Clean text by removing special characters, extra whitespace, etc.

    Args:
        text: Input text to clean
        remove_punctuation: Whether to remove punctuation (default: True)
        remove_numbers: Whether to remove numbers (default: False)

    Returns:
        Cleaned text string
    """
    if not isinstance(text, str):
        return ""

    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)

    if remove_numbers:
        text = re.sub(r'\d+', '', text)

    if remove_punctuation:
        text = text.translate(str.maketrans('', '', string.punctuation))

    text = re.sub(r'\s+', ' ', text).strip()
    return text


class TopicClusterer:
    """
    Clusters text data into topics using cosine similarity and k-means.

    Attributes:
        n_clusters: Number of topic clusters to create
        max_df: Maximum document frequency for TF-IDF vectorizer
        min_df: Minimum document frequency for TF-IDF vectorizer
        vectorizer: Fitted TF-IDF vectorizer
        kmeans: Fitted K-Means clustering model
        tfidf_matrix: TF-IDF vectors for the text data
    """

    def __init__(
        self,
        n_clusters: int = 5,
        max_df: float = 0.95,
        min_df: int = 1,
        random_state: int = 42,
        n_init: int = 10,
    ):
        self.n_clusters = n_clusters
        self.max_df = max_df
        self.min_df = min_df
        self.random_state = random_state
        self.n_init = n_init

        self.vectorizer = None
        self.kmeans = None
        self.tfidf_matrix = None
        self.feature_names = None

    def _preprocess_text(self, texts: List[str]) -> List[str]:
        processed = []
        for text in texts:
            if pd.isna(text):
                processed.append("")
            else:
                processed.append(str(text).lower().strip())
        return processed

    def fit(self, texts: List[str], show_progress: bool = True) -> 'TopicClusterer':
        if not texts or len(texts) == 0:
            raise ValueError("texts list cannot be empty")

        processed_texts = self._preprocess_text(texts)

        non_empty_texts = [t for t in processed_texts if t.strip()]
        if not non_empty_texts:
            raise ValueError("All texts are empty after preprocessing")

        self.vectorizer = TfidfVectorizer(
            max_df=self.max_df,
            min_df=self.min_df,
            stop_words='english',
            lowercase=True,
            max_features=500,
        )

        self.tfidf_matrix = self.vectorizer.fit_transform(processed_texts)
        self.feature_names = self.vectorizer.get_feature_names_out()

        self.kmeans = KMeans(
            n_clusters=min(self.n_clusters, len(non_empty_texts)),
            random_state=self.random_state,
            n_init=self.n_init,
        )
        self.kmeans.fit(self.tfidf_matrix)

        return self

    def predict(self, texts: List[str]) -> np.ndarray:
        if self.vectorizer is None or self.kmeans is None:
            raise ValueError("Model must be fitted before prediction. Call fit() first.")

        processed_texts = self._preprocess_text(texts)
        tfidf_new = self.vectorizer.transform(processed_texts)
        return self.kmeans.predict(tfidf_new)

    def fit_predict(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        self.fit(texts, show_progress=show_progress)
        return self.kmeans.labels_

    def get_top_terms(self, n_terms: int = 10) -> Dict[int, List[str]]:
        if self.kmeans is None or self.feature_names is None:
            raise ValueError("Model must be fitted first. Call fit() first.")

        cluster_centers = self.kmeans.cluster_centers_
        top_terms = {}

        for cluster_id in range(self.n_clusters):
            center = cluster_centers[cluster_id]
            top_indices = center.argsort()[-n_terms:][::-1]
            top_terms[cluster_id] = [
                self.feature_names[idx] for idx in top_indices
            ]

        return top_terms

    def get_cluster_distances(self, texts: List[str]) -> np.ndarray:
        if self.vectorizer is None or self.kmeans is None:
            raise ValueError("Model must be fitted first. Call fit() first.")

        processed_texts = self._preprocess_text(texts)
        tfidf_vectors = self.vectorizer.transform(processed_texts)

        similarities = cosine_similarity(tfidf_vectors, self.kmeans.cluster_centers_)
        distances = 1 - similarities
        return distances

    def get_2d_coordinates(self, texts: Optional[List[str]] = None) -> Tuple[np.ndarray, np.ndarray]:
        if self.tfidf_matrix is None or self.kmeans is None:
            raise ValueError("Model must be fitted first. Call fit() first.")

        if texts is not None:
            processed_texts = self._preprocess_text(texts)
            tfidf_vectors = self.vectorizer.transform(processed_texts)
            clusters = self.kmeans.predict(tfidf_vectors)
        else:
            tfidf_vectors = self.tfidf_matrix
            clusters = self.kmeans.labels_

        pca = PCA(n_components=2, random_state=self.random_state)
        coordinates_2d = pca.fit_transform(tfidf_vectors.toarray())

        return coordinates_2d, clusters

    def get_top_terms_matrix(self, n_terms: int = 10) -> pd.DataFrame:
        if self.kmeans is None or self.feature_names is None:
            raise ValueError("Model must be fitted first. Call fit() first.")

        cluster_centers = self.kmeans.cluster_centers_
        term_scores = {}

        for cluster_id in range(self.n_clusters):
            center = cluster_centers[cluster_id]
            top_indices = center.argsort()[-n_terms:][::-1]

            for rank, idx in enumerate(top_indices):
                term = self.feature_names[idx]
                score = center[idx]

                if term not in term_scores:
                    term_scores[term] = {}

                term_scores[term][cluster_id] = score

        df_terms = pd.DataFrame(term_scores).fillna(0).T
        columns_order = [col for col in range(self.n_clusters) if col in df_terms.columns]
        df_terms = df_terms[[col for col in columns_order if col in df_terms.columns]]

        return df_terms


def topic_cluster(
    file_path: Optional[str | Path] = None,
    text_column: Optional[str] = None,
    n_clusters: int = 5,
    max_df: float = 0.95,
    min_df: int = 1,
    n_init: int = 10,
    clean_text_option: bool = True,
    progress_callback=None,
) -> pd.DataFrame:
    """
    Perform topic clustering on a CSV column and return the DataFrame
    with a Cluster_Topic column appended.

    Args:
        file_path: Path to CSV file. If None, uses config.RAW_DATA_FILE.
        text_column: Name of the text column to cluster. If None, uses the
                     first object-type column found.
        n_clusters: Number of clusters to create (default: 5).
        max_df: Maximum document frequency (default: 0.95).
        min_df: Minimum document frequency (default: 1).
        n_init: Number of K-Means initializations (default: 10).
        clean_text_option: Whether to clean text before clustering (default: True).
        progress_callback: Optional callback(current, total, message).

    Returns:
        DataFrame with Cluster_Topic column and clusterer stored in df.attrs['clusterer'].
    """
    path = str(file_path) if file_path is not None else str(config.RAW_DATA_FILE)
    df = read_csv(path)

    # Auto-detect text column if not specified
    if text_column is None:
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        if not text_cols:
            raise ValueError("No text columns found in the dataset.")
        text_column = text_cols[0]

    if text_column not in df.columns:
        raise KeyError(f"Column '{text_column}' not found. Available: {list(df.columns)}")

    texts = df[text_column].tolist()

    if clean_text_option:
        texts = [clean_text(str(t)) for t in texts]

    clusterer = TopicClusterer(
        n_clusters=n_clusters,
        max_df=max_df,
        min_df=min_df,
        n_init=n_init,
    )

    clusters = clusterer.fit_predict(texts, show_progress=False)

    result_df = df.copy()
    result_df['Cluster_Topic'] = clusters

    # Store clusterer and text_column for visualization access
    result_df.attrs['clusterer'] = clusterer
    result_df.attrs['cluster_text_column'] = text_column

    return result_df

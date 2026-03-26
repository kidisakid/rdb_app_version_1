# Topic Clustering Module

**Module:** `src/clustering/topic_clustering.py`
**Category:** Analysis
**Version:** 1.0

---

## Purpose

The Topic Clustering module automatically groups text data (such as article headlines, summaries, or descriptions) into thematic clusters using machine learning. It applies TF-IDF vectorization and K-Means clustering to discover hidden topics within your media dataset, then provides rich visualizations to help you understand and present the results.

---

## When to Use

Use this module when:

- You want to discover what topics dominate your media coverage
- You need to categorize hundreds or thousands of articles into thematic groups automatically
- You are preparing a media analysis report and want to show topic distribution
- You want to identify emerging themes or underrepresented topics in coverage

---

## What It Does

1. **Text Cleaning (Optional)** — Removes HTML tags, URLs, email addresses, and optionally punctuation and numbers from the text before analysis.

2. **TF-IDF Vectorization** — Converts text into numerical feature vectors using Term Frequency-Inverse Document Frequency. This identifies the most distinctive words in each document relative to the entire corpus.

3. **K-Means Clustering** — Groups the vectorized texts into a specified number of clusters (default: 5). Each cluster represents a discovered topic.

4. **Cluster Assignment** — Adds a new `Cluster_Topic` column to your dataset with the assigned cluster number (0, 1, 2, ...) for each row.

5. **Visualization Suite** — Generates multiple charts and tables in the Streamlit interface:
   - Cluster distribution table and bar chart
   - Top terms (keywords) per cluster
   - PCA scatter plot showing cluster separation
   - Pie chart of cluster sizes
   - Heatmap of top terms by cluster
   - Model performance metrics (inertia, average distance)

---

## How to Use

### Via the Streamlit App (Recommended)

1. Upload your CSV or Excel file.
2. Check **"Topic clustering"** in the Analysis section of the sidebar.
3. Configure the clustering parameters:
   - **Text column**: Select which column contains the text to cluster (auto-detected if not specified)
   - **Number of clusters**: How many topic groups to create (2-20, default: 5)
   - **Max document frequency**: Ignore words appearing in more than this fraction of documents (default: 0.95)
   - **Min document frequency**: Ignore words appearing in fewer than this many documents (default: 1)
   - **K-Means initializations**: Number of times K-Means runs with different seeds (default: 10)
   - **Clean text**: Whether to remove HTML/URLs/punctuation before clustering (default: on)
4. Click **"Run Pipeline"**.
5. View the `Cluster_Topic` column in the results and explore the visualizations.

### Via Python (Programmatic)

```python
from src.clustering.topic_clustering import topic_cluster, TopicClusterer

# Quick pipeline usage
df = topic_cluster(
    file_path="data/raw/media_data.csv",
    text_column="Title",
    n_clusters=5,
    clean_text_option=True
)

# Access the trained clusterer for further analysis
clusterer = df.attrs['clusterer']
top_terms = clusterer.get_top_terms(n_terms=10)
for cluster_id, terms in top_terms.items():
    print(f"Cluster {cluster_id}: {', '.join(terms)}")

# Advanced: Use the TopicClusterer class directly
clusterer = TopicClusterer(n_clusters=8, max_df=0.9, min_df=2)
labels = clusterer.fit_predict(texts)
coords = clusterer.get_2d_coordinates()
```

---

## Input & Output

| Aspect       | Details                                                                   |
|-------------|---------------------------------------------------------------------------|
| **Input**   | A CSV or Excel file with at least one text column                         |
| **Output**  | A pandas DataFrame with a new `Cluster_Topic` column (integer 0, 1, 2...) |
| **Changes** | One new column added; original data untouched                             |
| **Extras**  | Clusterer object stored in `df.attrs['clusterer']` for visualization      |

### Example

**Input:**

| Title                                      | Source      |
|-------------------------------------------|-------------|
| Government approves new budget             | Daily News  |
| Election results show tight race           | Tribune     |
| New education policy announced             | Herald      |
| Stock market reaches all-time high         | Biz Daily   |
| Budget deficit grows amid spending         | Daily News  |

**Output (n_clusters=2):**

| Title                                      | Source      | Cluster_Topic |
|-------------------------------------------|-------------|---------------|
| Government approves new budget             | Daily News  | 0             |
| Election results show tight race           | Tribune     | 1             |
| New education policy announced             | Herald      | 1             |
| Stock market reaches all-time high         | Biz Daily   | 0             |
| Budget deficit grows amid spending         | Daily News  | 0             |

Cluster 0 might represent "Economy/Finance" topics, while Cluster 1 represents "Government/Policy" topics. The top terms per cluster will help you label them.

---

## Parameters

| Parameter            | Type       | Default   | Description                                          |
|---------------------|-----------|-----------|------------------------------------------------------|
| `file_path`          | `str`     | Config default | Path to the CSV or Excel file                    |
| `text_column`        | `str`     | Auto-detect | Column containing text to cluster                  |
| `n_clusters`         | `int`     | `5`       | Number of topic clusters to create                   |
| `max_df`             | `float`   | `0.95`    | Ignore words in more than this fraction of documents |
| `min_df`             | `int`     | `1`       | Ignore words in fewer than this many documents       |
| `n_init`             | `int`     | `10`      | Number of K-Means initializations                    |
| `clean_text_option`  | `bool`    | `True`    | Clean text before clustering                         |
| `progress_callback`  | `callable`| `None`    | Callback for progress updates                        |

---

## Configuration Defaults

The module has its own configuration file (`src/clustering/config.py`) with these defaults:

| Setting               | Value       | Description                                  |
|----------------------|-------------|----------------------------------------------|
| `DEFAULT_N_CLUSTERS`  | 5           | Default number of clusters                   |
| `DEFAULT_MAX_DF`      | 0.95        | Max document frequency threshold             |
| `DEFAULT_MIN_DF`      | 1           | Min document frequency threshold             |
| `TFIDF_MAX_FEATURES`  | 500         | Maximum vocabulary size                      |
| `TFIDF_STOP_WORDS`    | 'english'   | Stop word list for TF-IDF                    |
| `KMEANS_ALGORITHM`     | 'lloyd'     | K-Means algorithm variant                    |
| `REMOVE_PUNCTUATION`   | True        | Remove punctuation during text cleaning      |
| `REMOVE_NUMBERS`       | False       | Remove numbers during text cleaning          |
| `MIN_TOKEN_LENGTH`     | 3           | Minimum word length to keep                  |

---

## Visualizations Generated

When run via the Streamlit app, the following visualizations are automatically displayed:

| Visualization            | What It Shows                                                    |
|-------------------------|-------------------------------------------------------------------|
| **Distribution Table**   | Row count and percentage per cluster                             |
| **Bar Chart**           | Cluster sizes as horizontal bars                                  |
| **Top Terms**           | The 10 most distinctive keywords per cluster (helps you label them) |
| **PCA Scatter Plot**    | 2D projection of all documents, colored by cluster                |
| **Pie Chart**           | Proportional cluster sizes                                        |
| **Terms Heatmap**       | Heat map of term importance scores across all clusters            |
| **Inertia Score**       | K-Means inertia (lower = tighter clusters)                       |
| **Average Distance**    | Mean cosine distance (closer to 0 = better cluster fit)          |

---

## Understanding the Results

### How to Label Clusters

The module assigns numeric IDs (0, 1, 2, ...) to clusters. To give them meaningful names:

1. Check the **Top Terms** for each cluster — these are the most distinctive keywords.
2. Read a few sample articles from each cluster to confirm the theme.
3. Rename clusters in your downstream analysis or report (e.g., Cluster 0 = "Economy", Cluster 1 = "Politics").

### How to Choose the Right Number of Clusters

- **Start with 5** — This is the default and works well for most media datasets.
- **Too few clusters**: Topics feel too broad or mixed. Increase the count.
- **Too many clusters**: Topics start overlapping or feel arbitrary. Decrease the count.
- **Check inertia**: Lower inertia generally means better-defined clusters, but there are diminishing returns.

---

## Error Handling

- **No text column found**: If `text_column` is not specified, the module auto-detects the first column with string (object) dtype. If no string columns exist, it raises an error.
- **Empty text**: Rows with empty or null text values are handled gracefully — they may end up in a single "catch-all" cluster.
- **Too few documents**: If you have fewer documents than requested clusters, K-Means will produce fewer clusters than requested.

---

## Tips for Media Analysts

- **Choose the right text column** — Use article titles for broad topic discovery, or summaries/body text for more granular clustering.
- **Clean text first** — Leave the "Clean text" option enabled unless you have a specific reason not to. It removes noise (HTML, URLs) that can interfere with clustering.
- **Adjust max_df for common words** — If all your articles share domain-specific terms (like "media" or "news"), lower `max_df` to 0.85 to filter them out.
- **Run after other cleaning steps** — Normalize headers and remove duplicates before clustering to ensure clean, unique data.
- **Use top terms to understand clusters** — The automatically generated top terms are your key to interpreting what each cluster represents.
- **No internet required** — Unlike translation, clustering runs entirely locally on your machine.

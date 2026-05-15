"""
Recommendation Engine Module
Builds TF-IDF vectors from combined_features and computes cosine similarity.
Provides a recommend() function to fetch similar titles.
"""

import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Global variables for lazy loading
_df = None
_vectorizer = None
_tfidf_matrix = None
_cosine_sim = None
_indices = None
_loaded_csv_path = None
_loaded_csv_mtime = None


def _load_data(processed_csv_path):
    global _df, _vectorizer, _tfidf_matrix, _cosine_sim, _indices
    global _loaded_csv_path, _loaded_csv_mtime
    if not os.path.exists(processed_csv_path):
        raise FileNotFoundError(f"Processed dataset not found at {processed_csv_path}")

    csv_mtime = os.path.getmtime(processed_csv_path)
    if (
        _df is not None
        and _loaded_csv_path == processed_csv_path
        and _loaded_csv_mtime == csv_mtime
    ):
        return

    _df = pd.read_csv(processed_csv_path)
    # Ensure combined_features exists
    if "combined_features" not in _df.columns:
        raise ValueError("Dataset missing 'combined_features' column. Run preprocessing first.")

    # Drop rows with empty combined_features
    _df = _df[_df["combined_features"].fillna("").str.len() > 0].reset_index(drop=True)

    _vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    _tfidf_matrix = _vectorizer.fit_transform(_df["combined_features"])
    _cosine_sim = cosine_similarity(_tfidf_matrix, _tfidf_matrix)
    _indices = pd.Series(_df.index, index=_df["title"]).to_dict()
    _loaded_csv_path = processed_csv_path
    _loaded_csv_mtime = csv_mtime


def recommend(title, top_n=5, processed_csv_path=None):
    """
    Recommend similar entertainment content based on cosine similarity.

    Args:
        title (str): Exact or case-insensitive title from the dataset.
        top_n (int): Number of recommendations to return.
        processed_csv_path (str): Path to processed CSV. Auto-detected if None.

    Returns:
        list of dicts with title, genre, rating, description, similarity_score
    """
    if processed_csv_path is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        processed_csv_path = os.path.join(base, "data", "processed", "entertainment_data.csv")
        if not os.path.exists(processed_csv_path):
            processed_csv_path = r"C:\Users\thaku\entertainment-recommender\data\processed\entertainment_data.csv"

    _load_data(processed_csv_path)

    # Normalize input title for matching
    title_clean = title.lower().strip()
    # Try exact match first, then partial
    matched_title = None
    if title_clean in _indices:
        matched_title = title_clean
    else:
        for t in _indices.keys():
            if title_clean == t or title_clean in t:
                matched_title = t
                break

    if matched_title is None:
        return []

    idx = _indices[matched_title]
    sim_scores = list(enumerate(_cosine_sim[idx]))
    # Sort by similarity descending, exclude the item itself
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = [s for s in sim_scores if s[0] != idx]
    top_scores = sim_scores[:top_n]

    results = []
    for i, score in top_scores:
        row = _df.iloc[i]
        results.append({
            "title": row.get("title", ""),
            "genre": row.get("genre", ""),
            "rating": row.get("rating", None),
            "description": row.get("description", ""),
            "similarity_score": round(float(score), 4),
            "source": row.get("source", ""),
            "language": row.get("language", ""),
            "duration": row.get("duration", None),
            "episodes": row.get("episodes", None),
            "poster_url": row.get("poster_url", ""),
        })
    return results


if __name__ == "__main__":
    import sys
    test_title = sys.argv[1] if len(sys.argv) > 1 else "the godfather"
    recs = recommend(test_title, top_n=5)
    print(f"Recommendations for '{test_title}':")
    for r in recs:
        print(f"  {r['title']} | sim={r['similarity_score']} | genre={r['genre']} | rating={r['rating']}")

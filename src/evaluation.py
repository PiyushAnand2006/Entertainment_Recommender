"""
Evaluation Module
Computes Precision@K and NDCG@K for the content-based recommender
using genre overlap as the relevance signal.
"""

import os
import sys
import numpy as np
import pandas as pd
from math import log2

# Ensure src is on path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import recommendation_engine
from recommendation_engine import recommend, _load_data


def _genre_set(genre_str):
    """Convert a genre string into a set of normalized tokens."""
    if pd.isna(genre_str) or not str(genre_str).strip():
        return set()
    raw = str(genre_str).lower()
    for sep in [",", "/", "-", "&", "|"]:
        raw = raw.replace(sep, " ")
    return {g.strip() for g in raw.split() if g.strip()}


def genre_overlap(g1, g2):
    """Return True if two genre strings share at least one token."""
    return len(_genre_set(g1) & _genre_set(g2)) > 0


def dcg_at_k(relevances, k):
    """Compute Discounted Cumulative Gain at K."""
    rel = np.array(relevances[:k], dtype=float)
    if rel.size == 0:
        return 0.0
    positions = np.arange(1, k + 1)
    discounts = np.log2(positions + 1)
    return float(np.sum(rel / discounts))


def precision_at_k(query_title, k=5, processed_csv_path=None):
    """
    Precision@K for a single query.
    A recommendation is relevant if it shares at least one genre token with the query.
    """
    recs = recommend(query_title, top_n=k, processed_csv_path=processed_csv_path)
    if not recs:
        return 0.0

    # _load_data is called inside recommend, so _df should be populated
    query_row = recommendation_engine._df[recommendation_engine._df["title"] == query_title]
    if query_row.empty:
        return 0.0
    query_genre = query_row.iloc[0]["genre"]

    relevant = [genre_overlap(query_genre, r["genre"]) for r in recs]
    return sum(relevant) / k


def ndcg_at_k(query_title, k=5, processed_csv_path=None):
    """
    NDCG@K for a single query.
    Binary relevance based on genre overlap.
    """
    recs = recommend(query_title, top_n=k, processed_csv_path=processed_csv_path)
    if not recs:
        return 0.0

    query_row = recommendation_engine._df[recommendation_engine._df["title"] == query_title]
    if query_row.empty:
        return 0.0
    query_genre = query_row.iloc[0]["genre"]

    relevances = [1.0 if genre_overlap(query_genre, r["genre"]) else 0.0 for r in recs]
    dcg = dcg_at_k(relevances, k)

    num_relevant = int(sum(relevances))
    ideal = [1.0] * num_relevant + [0.0] * (k - num_relevant)
    ideal = ideal[:k]
    idcg = dcg_at_k(ideal, k)

    if idcg == 0:
        return 0.0
    return dcg / idcg


def evaluate_system(k_values=(5, 10), sample_size=None, processed_csv_path=None):
    """
    Run evaluation across all (or sampled) titles and report averaged metrics.

    Returns:
        dict: metric_name -> mean value
        list: titles that were evaluated
    """
    if processed_csv_path is None:
        processed_csv_path = os.path.join(BASE_DIR, "data", "processed", "entertainment_data.csv")
        if not os.path.exists(processed_csv_path):
            processed_csv_path = r"C:\Users\thaku\entertainment-recommender\data\processed\entertainment_data.csv"

    _load_data(processed_csv_path)
    all_titles = list(recommendation_engine._df["title"].unique())

    if sample_size and 0 < sample_size < len(all_titles):
        rng = np.random.default_rng(seed=42)
        titles = rng.choice(all_titles, size=sample_size, replace=False).tolist()
    else:
        titles = all_titles

    results = {}
    for k in k_values:
        precisions = []
        ndcgs = []
        for t in titles:
            try:
                precisions.append(precision_at_k(t, k=k, processed_csv_path=processed_csv_path))
                ndcgs.append(ndcg_at_k(t, k=k, processed_csv_path=processed_csv_path))
            except Exception:
                # Skip titles that cause errors (e.g., missing data)
                continue

        results[f"Precision@{k}"] = round(float(np.mean(precisions)), 4) if precisions else 0.0
        results[f"NDCG@{k}"]       = round(float(np.mean(ndcgs)), 4) if ndcgs else 0.0
        results[f"Precision@{k}_std"] = round(float(np.std(precisions)), 4) if precisions else 0.0
        results[f"NDCG@{k}_std"]       = round(float(np.std(ndcgs)), 4) if ndcgs else 0.0
        results[f"n_evaluated"] = len(precisions)

    return results, titles


def print_report(results):
    """Pretty-print evaluation results."""
    n = results.get("n_evaluated", 0)
    print(f"\nEvaluation Report (n={n} titles)")
    print("=" * 40)
    for k in sorted({int(key.split("@")[1].split("_")[0]) for key in results if "@" in key and "_" not in key.split("@")[1]}):
        print(f"\n@K = {k}")
        print(f"  Precision@{k} : {results[f'Precision@{k}']}  (+/- {results[f'Precision@{k}_std']})")
        print(f"  NDCG@{k}      : {results[f'NDCG@{k}']}  (+/- {results[f'NDCG@{k}_std']})")


if __name__ == "__main__":
    print("Running evaluation...")
    metrics, eval_titles = evaluate_system(k_values=[5, 10], sample_size=200)
    print_report(metrics)

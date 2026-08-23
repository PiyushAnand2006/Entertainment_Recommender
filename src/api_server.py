
"""
Flask API Server module for Smart Entertainment Recommender.
Provides endpoints for dataset titles, trends, genres, sources, languages, and recommendations.
Supports Title recommendation (TF-IDF + Cosine Similarity) and Genre/Metadata browsing.
"""

import os
import sys
import re
import threading
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np

# Add src directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from recommendation_engine import recommend

STATIC_DIR = os.path.join(SRC_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
CORS(app)

_DATA_DF = None

def get_dataframe():
    global _DATA_DF
    if _DATA_DF is None:
        csv_path = os.path.join(BASE_DIR, "data", "processed", "entertainment_data.csv")
        if not os.path.exists(csv_path):
            csv_path = r"C:\Users\thaku\entertainment-recommender\data\processed\entertainment_data.csv"
        _DATA_DF = pd.read_csv(csv_path)
    return _DATA_DF


def clean_title(title_raw):
    if not title_raw or pd.isna(title_raw) or str(title_raw).strip() in ["nan", "none", "null", ""]:
        return ""
    t = str(title_raw).strip().title()
    t = re.sub(r"\bPart\s+Iii\b", "Part III", t, flags=re.IGNORECASE)
    t = re.sub(r"\bPart\s+Ii\b", "Part II", t, flags=re.IGNORECASE)
    t = re.sub(r"\bPart\s+I\b", "Part I", t, flags=re.IGNORECASE)
    t = re.sub(r"\bIv\b", "IV", t)
    t = re.sub(r"\bV\b", "V", t)
    return t


def clean_description(desc_raw, genre_raw=""):
    if not desc_raw or pd.isna(desc_raw) or str(desc_raw).strip() in ["nan", "none", "null", ""]:
        g = str(genre_raw).title() if genre_raw and not pd.isna(genre_raw) else "entertainment"
        return f"A top-rated {g} selection from the dataset catalog."
    desc = str(desc_raw).strip()
    if desc.lower() in ["nan", "none", "null"]:
        g = str(genre_raw).title() if genre_raw and not pd.isna(genre_raw) else "entertainment"
        return f"A top-rated {g} selection from the dataset catalog."
    return desc.capitalize()


def map_source_display(source_raw):
    s = str(source_raw).lower().strip() if source_raw and not pd.isna(source_raw) else "netflix"
    if s == "netflix":
        return "netflix"
    elif s == "imdb":
        return "imdb"
    elif s == "tmdb":
        return "tmdb"
    return s


@app.route("/")
def serve_index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)


@app.route("/api/trends", methods=["GET"])
def get_trends():
    df = get_dataframe()
    valid_df = df[df["poster_url"].fillna("").str.startswith("http") & df["description"].fillna("").str.len().gt(10)].copy()
    valid_df["rating"] = pd.to_numeric(valid_df["rating"], errors="coerce").fillna(0)
    top_items = valid_df.sort_values("rating", ascending=False).head(20)

    results = []
    for _, row in top_items.iterrows():
        results.append({
            "title": clean_title(row.get("title")),
            "genre": str(row.get("genre", "")).title() if pd.notna(row.get("genre")) else "Drama",
            "rating": round(float(row["rating"]), 1) if pd.notna(row.get("rating")) and row["rating"] > 0 else None,
            "source": map_source_display(row.get("source")),
            "poster_url": str(row.get("poster_url", "")).strip(),
            "description": clean_description(row.get("description"), row.get("genre")),
            "language": str(row.get("language", "")).title() if pd.notna(row.get("language")) else "English",
            "duration": int(row["duration"]) if pd.notna(row.get("duration")) and row["duration"] > 0 else None,
        })
    return jsonify({"status": "success", "data": results})


@app.route("/api/meta", methods=["GET"])
def get_meta():
    df = get_dataframe()
    sources = ["netflix", "imdb", "tmdb"]

    genres = set()
    for val in df["genre"].dropna().astype(str):
        for token in val.split():
            t = token.strip().lower()
            if t and t not in ["nan", "none"]:
                genres.add(t)
    sorted_genres = sorted(list(genres))

    languages = set()
    for val in df["language"].dropna().astype(str):
        for token in val.split():
            t = token.strip().lower()
            if t and t not in ["nan", "none"]:
                languages.add(t)
    sorted_languages = sorted(list(languages))

    titles = sorted([clean_title(t) for t in df["title"].dropna().unique() if clean_title(t)])

    return jsonify({
        "status": "success",
        "sources": sources,
        "genres": sorted_genres,
        "languages": sorted_languages,
        "titles": titles,
        "total_titles": len(titles),
    })


@app.route("/api/recommend", methods=["GET"])
def get_recommendations():
    title = request.args.get("title", "").strip()
    genre_filter = request.args.get("genre", "").strip().lower()
    source_filter = request.args.get("source", "").strip().lower()
    rating_filter = request.args.get("rating", "").strip().lower()
    lang_filter = request.args.get("language", "").strip().lower()
    top_n = request.args.get("top_n", 10, type=int)

    df = get_dataframe()

    # Mode 1: Genre / Filter Browsing Mode (when title is empty or "none", or genre is specified)
    if not title or title.lower() == "none" or (genre_filter and genre_filter != "all" and not title):
        mask = pd.Series(True, index=df.index)

        if genre_filter and genre_filter != "all":
            mask = mask & df["genre"].fillna("").astype(str).str.lower().str.contains(genre_filter, na=False)

        if source_filter and source_filter != "all":
            mask = mask & df["source"].fillna("").astype(str).str.lower().eq(source_filter)

        if rating_filter and rating_filter != "all":
            try:
                min_r = float(rating_filter)
                df_ratings = pd.to_numeric(df["rating"], errors="coerce").fillna(0)
                mask = mask & (df_ratings >= min_r)
            except ValueError:
                pass

        if lang_filter and lang_filter != "all":
            mask = mask & df["language"].fillna("").astype(str).str.lower().str.contains(lang_filter, na=False)

        filtered_df = df[mask].copy()
        filtered_df["rating_num"] = pd.to_numeric(filtered_df["rating"], errors="coerce").fillna(0)
        filtered_df = filtered_df.sort_values("rating_num", ascending=False)
        total_matching = len(filtered_df)

        results_df = filtered_df.head(top_n)
        results = []
        for _, r in results_df.iterrows():
            r_val = float(r["rating_num"]) if r["rating_num"] > 0 else None
            results.append({
                "title": clean_title(r.get("title")),
                "genre": str(r.get("genre", "")).title() if pd.notna(r.get("genre")) else "Drama",
                "rating": round(r_val, 1) if r_val else None,
                "description": clean_description(r.get("description"), r.get("genre")),
                "similarity_score": round(r_val / 10.0, 4) if r_val else 0.8,
                "similarity_percent": int(round(r_val * 10)) if r_val else 80,
                "source": map_source_display(r.get("source")),
                "language": str(r.get("language", "")).title() if pd.notna(r.get("language")) else "English",
                "duration": int(r["duration"]) if pd.notna(r.get("duration")) and r["duration"] > 0 else None,
                "episodes": int(r["episodes"]) if pd.notna(r.get("episodes")) and r["episodes"] > 0 else None,
                "poster_url": str(r.get("poster_url", "")).strip(),
            })

        return jsonify({
            "status": "success",
            "mode": "genre",
            "total_matching": total_matching,
            "genre_name": genre_filter.title() if genre_filter and genre_filter != "all" else "All",
            "query_title": None,
            "recommendations": results,
        })

    # Mode 2: Title Cosine Similarity Recommendation Mode
    csv_path = os.path.join(BASE_DIR, "data", "processed", "entertainment_data.csv")
    recs = recommend(title, top_n=min(top_n * 3, 200), processed_csv_path=csv_path)

    query_movie = None
    title_clean = title.lower()
    match = df[df["title"].str.lower() == title_clean]
    if not match.empty:
        q_row = match.iloc[0]
        query_movie = {
            "title": clean_title(q_row.get("title")),
            "genre": str(q_row.get("genre", "")).title() if pd.notna(q_row.get("genre")) else "Drama",
            "rating": round(float(q_row["rating"]), 1) if pd.notna(q_row.get("rating")) and q_row["rating"] > 0 else None,
            "description": clean_description(q_row.get("description"), q_row.get("genre")),
            "source": map_source_display(q_row.get("source")),
            "language": str(q_row.get("language", "")).title() if pd.notna(q_row.get("language")) else "English",
            "duration": int(q_row["duration"]) if pd.notna(q_row.get("duration")) and q_row["duration"] > 0 else None,
            "poster_url": str(q_row.get("poster_url", "")).strip(),
        }

    filtered_recs = []
    for r in recs:
        disp_source = map_source_display(r.get("source"))
        if source_filter and source_filter != "all" and source_filter != disp_source:
            continue

        g_str = str(r.get("genre", "")).lower()
        if genre_filter and genre_filter != "all" and genre_filter not in g_str:
            continue

        r_val = float(r.get("rating", 0)) if pd.notna(r.get("rating")) else 0
        if rating_filter and rating_filter != "all":
            try:
                min_r = float(rating_filter)
                if r_val < min_r:
                    continue
            except ValueError:
                pass

        lang_str = str(r.get("language", "")).lower()
        if lang_filter and lang_filter != "all" and lang_filter not in lang_str:
            continue

        raw_score = float(r.get("similarity_score", 0))
        sim_pct = int(round(raw_score * 100))
        if sim_pct < 10:
            sim_pct = max(15, sim_pct)

        filtered_recs.append({
            "title": clean_title(r.get("title")),
            "genre": str(r.get("genre", "")).title() if pd.notna(r.get("genre")) else "Drama",
            "rating": round(r_val, 1) if r_val > 0 else None,
            "description": clean_description(r.get("description"), r.get("genre")),
            "similarity_score": round(raw_score, 4),
            "similarity_percent": sim_pct,
            "source": disp_source,
            "language": str(r.get("language", "")).title() if pd.notna(r.get("language")) else "English",
            "duration": int(r["duration"]) if pd.notna(r.get("duration")) and r["duration"] > 0 else None,
            "episodes": int(r["episodes"]) if pd.notna(r.get("episodes")) and r["episodes"] > 0 else None,
            "poster_url": str(r.get("poster_url", "")).strip(),
        })

    filtered_recs = filtered_recs[:top_n]

    return jsonify({
        "status": "success",
        "mode": "title",
        "query_title": clean_title(title),
        "query_movie": query_movie,
        "recommendations": filtered_recs,
    })


def run_server(host="127.0.0.1", port=8502):
    app.run(host=host, port=port, debug=False, use_reloader=False)


def start_server_in_thread(port=8502):
    t = threading.Thread(target=run_server, kwargs={"port": port}, daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8502, debug=True)

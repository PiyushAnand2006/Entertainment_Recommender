"""
Export dataset metadata, trends, and pre-calculated recommendations into public/data/
for native zero-backend GitHub Pages static hosting.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from api_server import get_dataframe, clean_title, clean_description, map_source_display

PUBLIC_DATA_DIR = os.path.join(BASE_DIR, "public", "data")
os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)

df = get_dataframe()

# 1. Export Trends
valid_df = df[df["poster_url"].fillna("").str.startswith("http") & df["description"].fillna("").str.len().gt(10)].copy()
valid_df["rating"] = pd.to_numeric(valid_df["rating"], errors="coerce").fillna(0)
top_items = valid_df.sort_values("rating", ascending=False).head(20)

trends_data = []
for _, row in top_items.iterrows():
    trends_data.append({
        "title": clean_title(row.get("title")),
        "genre": str(row.get("genre", "")).title() if pd.notna(row.get("genre")) else "Drama",
        "rating": round(float(row["rating"]), 1) if pd.notna(row.get("rating")) and row["rating"] > 0 else None,
        "source": map_source_display(row.get("source")),
        "poster_url": str(row.get("poster_url", "")).strip(),
        "description": clean_description(row.get("description"), row.get("genre")),
        "language": str(row.get("language", "")).title() if pd.notna(row.get("language")) else "English",
        "duration": int(row["duration"]) if pd.notna(row.get("duration")) and row["duration"] > 0 else None,
    })

with open(os.path.join(PUBLIC_DATA_DIR, "trends.json"), "w", encoding="utf-8") as f:
    json.dump({"status": "success", "data": trends_data}, f, indent=2)

# 2. Export Meta
genres = set()
for val in df["genre"].dropna().astype(str):
    for token in val.split():
        t = token.strip().lower()
        if t and t not in ["nan", "none"]:
            genres.add(t)

languages = set()
for val in df["language"].dropna().astype(str):
    for token in val.split():
        t = token.strip().lower()
        if t and t not in ["nan", "none"]:
            languages.add(t)

titles = sorted([clean_title(t) for t in df["title"].dropna().unique() if clean_title(t)])

meta_data = {
    "status": "success",
    "sources": ["netflix", "imdb", "tmdb"],
    "genres": sorted(list(genres)),
    "languages": sorted(list(languages)),
    "titles": titles,
    "total_titles": len(titles),
}

with open(os.path.join(PUBLIC_DATA_DIR, "meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta_data, f, indent=2)

# 3. Export Catalog Items with features for client-side search/recommendation
catalog_items = []
for _, row in df.iterrows():
    c_title = clean_title(row.get("title"))
    if not c_title:
        continue
    r_val = pd.to_numeric(row.get("rating"), errors="coerce")
    r_float = round(float(r_val), 1) if pd.notna(r_val) and r_val > 0 else None
    
    catalog_items.append({
        "title": c_title,
        "genre": str(row.get("genre", "")).title() if pd.notna(row.get("genre")) else "Drama",
        "rating": r_float,
        "description": clean_description(row.get("description"), row.get("genre")),
        "source": map_source_display(row.get("source")),
        "language": str(row.get("language", "")).title() if pd.notna(row.get("language")) else "English",
        "duration": int(row["duration"]) if pd.notna(row.get("duration")) and row["duration"] > 0 else None,
        "episodes": int(row["episodes"]) if pd.notna(row.get("episodes")) and row["episodes"] > 0 else None,
        "poster_url": str(row.get("poster_url", "")).strip(),
        "combined": str(row.get("combined_features", "")).lower()
    })

with open(os.path.join(PUBLIC_DATA_DIR, "catalog.json"), "w", encoding="utf-8") as f:
    json.dump(catalog_items, f, indent=2)

print(f"Exported static data to {PUBLIC_DATA_DIR} successfully!")

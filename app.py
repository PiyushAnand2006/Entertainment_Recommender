"""
Attractive Streamlit UI for Smart Entertainment Recommendation System.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import pandas as pd
import streamlit as st
from recommendation_engine import recommend

# custom CSS for dark cards, badges, and layout
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* card container */
.card {
    background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
    border: 1px solid #374151;
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    color: #f3f4f6;
    transition: transform .15s ease;
}
.card:hover { transform: translateY(-3px); border-color: #60a5fa; }

/* rank badge */
.rank-badge {
    display: inline-block;
    background: #60a5fa;
    color: #0f172a;
    font-weight: 700;
    border-radius: 50%;
    width: 32px; height: 32px;
    line-height: 32px;
    text-align: center;
    margin-right: .6rem;
    font-size: .9rem;
}

/* title */
.card-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #f9fafb;
    letter-spacing: .2px;
}

/* score pill */
.score-pill {
    display: inline-block;
    background: #10b981;
    color: #064e3b;
    font-weight: 700;
    border-radius: 999px;
    padding: .25rem .7rem;
    font-size: .85rem;
}
.rating-pill {
    display: inline-block;
    background: #f59e0b;
    color: #78350f;
    font-weight: 700;
    border-radius: 999px;
    padding: .25rem .7rem;
    font-size: .85rem;
}

/* meta chips */
.chip {
    display: inline-block;
    background: #374151;
    color: #e5e7eb;
    border-radius: 6px;
    padding: .2rem .5rem;
    font-size: .75rem;
    margin-right: .35rem;
    margin-bottom: .35rem;
}

/* description text */
.card-desc {
    color: #9ca3af;
    font-size: .88rem;
    line-height: 1.45;
    margin-top: .6rem;
}

/* sidebar background & text */
[data-testid="stSidebar"] { background: #0f172a !important; }
[data-testid="stSidebar"] .block-container { color: #e2e8f0; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiselect label,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h4 {
    color: #f8fafc !important;
}
[data-testid="stSidebar"] .stSlider > div[data-testid="stTickBar"] { color: #94a3b8; }
[data-testid="stSidebar"] .stButton button,
[data-testid="stSidebar"] .stButton button p {
    color: #000000 !important;
    background: #e2e8f0 !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)


def _extract_genres(series):
    tokens = set()
    for val in series.dropna().astype(str).str.strip():
        if val:
            tokens.update([t for t in val.split() if t])
    return sorted(tokens)


def _genre_color(genre):
    cmap = {
        "action": "#ef4444", "adventure": "#f97316", "comedy": "#f59e0b",
        "crime": "#84cc16", "drama": "#06b6d4", "fantasy": "#8b5cf6",
        "horror": "#ec4899", "mystery": "#6366f1", "romance": "#f43f5e",
        "sci-fi": "#3b82f6", "thriller": "#14b8a6", "documentary": "#64748b",
        "war": "#78716c", "animation": "#a855f7", "family": "#22c55e",
        "western": "#b45309", "biography": "#0ea5e9", "history": "#64748b",
        "musical": "#d946ef", "sport": "#10b981",
    }
    key = str(genre).lower().strip() if genre else ""
    return cmap.get(key, "#6b7280")


def _render_card(i, row, show_similarity=True):
    title = str(row.get("title", "")).title()
    genre = str(row.get("genre", "")).title() if row.get("genre") else "N/A"
    source = str(row.get("source", "")).upper() if row.get("source") else "N/A"
    rating = row.get("rating")
    rating_str = f"{float(rating):.1f}" if pd.notna(rating) else "N/A"
    lang = str(row.get("language", "")).title() if row.get("language") else "N/A"
    dur = int(row["duration"]) if pd.notna(row.get("duration")) else None
    dur_str = f"{dur} min" if dur else "N/A"
    eps = int(row["episodes"]) if pd.notna(row.get("episodes")) else "N/A"
    desc = str(row.get("description", "")).strip()
    desc_html = f'<div class="card-desc">{desc.capitalize()}</div>' if desc else ""

    score_html = ""
    if show_similarity and pd.notna(row.get("similarity_score")):
        score_html = f'<span class="score-pill">Similarity: {float(row["similarity_score"]):.3f}</span>'
    elif pd.notna(rating):
        score_html = f'<span class="rating-pill">IMDb: {rating_str}</span>'

    poster_raw = row.get("poster_url", "")
    poster = str(poster_raw).strip() if pd.notna(poster_raw) else ""
    if poster and poster.lower().startswith("http"):
        poster_html = f'<img src="{poster}" alt="poster" style="width:80px; height:110px; object-fit:cover; border-radius:10px; margin-right:1rem;">'
    else:
        poster_html = '<div style="width:80px; height:110px; background:#374151; border-radius:10px; margin-right:1rem; display:flex; align-items:center; justify-content:center; color:#6b7280; font-size:.7rem;">No poster</div>'

    html = f"""
    <div class="card">
        <div style="display:flex; align-items:flex-start;">
            {poster_html}
            <div style="flex:1;">
                <div style="display:flex; align-items:center; justify-content:space-between;">
                    <div style="display:flex; align-items:center;">
                        <span class="rank-badge">{i}</span>
                        <span class="card-title">{title}</span>
                    </div>
                    <div>{score_html}</div>
                </div>
                <div style="margin-top:.7rem;">
                    <span class="chip" style="background:{_genre_color(row.get('genre',''))}22; color:{_genre_color(row.get('genre',''))}; border:1px solid {_genre_color(row.get('genre',''))}44;">{genre}</span>
                    <span class="chip">{source}</span>
                    <span class="chip">{lang}</span>
                    <span class="chip">{dur_str}</span>
                    <span class="chip">Ep: {eps}</span>
                </div>
                {desc_html}
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


st.set_page_config(page_title="Smart Entertainment Recommender", layout="wide", initial_sidebar_state="expanded")

col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.markdown("<h1 style='font-size:2.8rem; margin:0;'>🎬</h1>", unsafe_allow_html=True)
with col_title:
    st.markdown("""
        <h1 style='margin-bottom:.2rem; color:#1f2937;'>Smart Entertainment Recommender</h1>
        <p style='color:#4b5563; margin-top:0;'>Discover movies & shows using TF-IDF + Cosine Similarity</p>
    """, unsafe_allow_html=True)

st.markdown("---")

processed_path = os.path.join(BASE_DIR, "data", "processed", "entertainment_data.csv")
if not os.path.exists(processed_path):
    processed_path = r"C:\Users\thaku\entertainment-recommender\data\processed\entertainment_data.csv"

if not os.path.exists(processed_path):
    st.error("Processed dataset not found. Please run `data_preprocessing.py` first.")
    st.stop()

_df = pd.read_csv(processed_path)
titles = sorted([t for t in _df["title"].dropna().unique().tolist() if str(t).strip() != ""])

with st.sidebar:
    st.markdown("<h2 style='color:#f9fafb;'>Settings</h2>", unsafe_allow_html=True)
    selected_title = st.selectbox("Select a Title", titles, index=0)
    top_n = st.slider("Number of Results", 1, 20, 5)

    st.markdown("<hr style='border-color:#374151;'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#f9fafb;'>Filters</h4>", unsafe_allow_html=True)

    source_filter = st.multiselect("Source", sorted(_df["source"].dropna().unique().tolist()), default=[])
    genre_options = [g.title() for g in _extract_genres(_df["genre"])]
    selected_genre = st.selectbox("Browse by Genre", ["None"] + genre_options, index=0)

    st.markdown("<hr style='border-color:#374151;'>", unsafe_allow_html=True)
    go = st.button("Recommend", use_container_width=True)
    st.markdown("<p style='font-size:.75rem; color:#6b7280; margin-top:1rem;'>Built with Python, scikit-learn & Streamlit</p>", unsafe_allow_html=True)

if go:
    if selected_genre != "None":
        genre_lower = selected_genre.lower()
        mask = _df["genre"].str.contains(genre_lower, na=False)
        if source_filter:
            mask = mask & _df["source"].isin(source_filter)
        genre_df = _df[mask].copy()
        genre_df["rating"] = pd.to_numeric(genre_df["rating"], errors="coerce")
        genre_df = genre_df.sort_values("rating", ascending=False).head(top_n)

        if genre_df.empty:
            st.warning(f"No titles found for genre **{selected_genre}**.")
        else:
            st.markdown(f"<h3 style='color:#10b981;'>{len(genre_df)} titles in <b>{selected_genre}</b></h3>", unsafe_allow_html=True)
            for i, (_, row) in enumerate(genre_df.iterrows(), start=1):
                _render_card(i, row, show_similarity=False)
    else:
        with st.spinner("Finding similar content..."):
            results = recommend(selected_title, top_n=top_n, processed_csv_path=processed_path)

        if not results:
            st.warning("No recommendations found. Try a different title.")
        else:
            if source_filter:
                results = [r for r in results if r.get("source", "") in source_filter]

            qg = ""
            if selected_title in _df["title"].values:
                raw = _df.loc[_df["title"] == selected_title, "genre"].values[0]
                qg = str(raw).title() if pd.notna(raw) and str(raw).strip() else "N/A"
            st.markdown(f"<h3 style='color:#60a5fa;'>Recommendations for <b>{selected_title.title()}</b> <span style='font-size:.85rem; color:#9ca3af;'>(Genre: {qg})</span></h3>", unsafe_allow_html=True)
            for i, r in enumerate(results, start=1):
                _render_card(i, r, show_similarity=True)
else:
    st.info("Select a title or pick a genre, then click **Recommend** to get started.")

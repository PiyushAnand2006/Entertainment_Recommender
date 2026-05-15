"""
Data Preprocessing Module
Loads NetflixOriginals.xlsx and imdb_top_1000.xlsx,
standardizes columns, cleans text, creates combined_features,
and saves the processed dataset.
"""

import pandas as pd
import numpy as np
import re
import os


HINDI_IMDB_TITLES = {
    "3 idiots", "a wednesday", "airlift", "anand", "andaz apna apna",
    "andhadhun", "baby", "badhaai ho", "bajrangi bhaijaan", "barfi",
    "bhaag milkha bhaag", "black", "chak de india", "chhichhore", "dangal",
    "dev d", "dil bechara", "dil chahta hai", "dilwale dulhania le jayenge",
    "gangs of wasseypur", "gully boy", "haider", "hera pheri", "jab we met",
    "kahaani", "kai po che", "kal ho naa ho",
    "lagaan once upon a time in india", "lage raho munna bhai",
    "m s dhoni the untold story", "munna bhai m b b s", "my name is khan",
    "omg oh my god", "paan singh tomar", "pink", "pk", "queen", "raazi",
    "rang de basanti", "rockstar", "sholay", "special chabbis",
    "swades we the people", "taare zameen par", "talvar", "the lunchbox",
    "udaan", "udta punjab", "uri the surgical strike", "veer zaara",
    "vicky donor", "zindagi na milegi dobara",
}

IMDB_LANGUAGE_OVERRIDES = {
    **{title: "hindi" for title in HINDI_IMDB_TITLES},
    "b hubali the beginning": "telugu",
    "baahubali 2 the conclusion": "telugu",
    "drishyam": "malayalam",
    "soorarai pottru": "tamil",
    "vikram vedha": "tamil",
}


def clean_text(text):
    """Lowercase, remove special chars, extra spaces."""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_netflix(path):
    df = pd.read_excel(path)
    df = df.rename(columns={
        "Title": "title",
        "Genre": "genre",
        "Language": "language",
        "Length": "duration",
        "EpisodesParsed": "episodes",
    })
    # Netflix lacks description, cast, rating -> fill defaults or infer
    df["description"] = ""
    # Use GenreLabels as keywords proxy if available
    if "GenreLabels" in df.columns:
        df["keywords"] = df["GenreLabels"].fillna("").astype(str)
    else:
        df["keywords"] = df["genre"].fillna("").astype(str)
    df["cast"] = ""
    df["rating"] = np.nan
    df["source"] = "netflix"
    df["poster_url"] = ""
    return df


def load_imdb(path):
    df = pd.read_excel(path)
    df = df.rename(columns={
        "Series_Title": "title",
        "Genre": "genre",
        "Runtime": "duration",
        "Overview": "description",
        "IMDB_Rating": "rating",
        "Poster_Link": "poster_url",
    })
    # No language column in IMDB dataset; assume English for most top IMDB entries
    df["language"] = "english"
    # Movies -> episodes = 1 (default), since column doesn't exist
    df["episodes"] = 1
    # Build cast from Star1..Star4
    stars = ["Star1", "Star2", "Star3", "Star4"]
    available_stars = [s for s in stars if s in df.columns]
    if available_stars:
        df["cast"] = df[available_stars].apply(
            lambda row: ", ".join([str(x) for x in row if pd.notna(x)]), axis=1
        )
    else:
        df["cast"] = ""
    df["keywords"] = df["genre"].fillna("").astype(str)
    df["source"] = "imdb"
    if "poster_url" not in df.columns:
        df["poster_url"] = ""
    return df


def preprocess_dataset(netflix_path, imdb_path, output_path):
    netflix = load_netflix(netflix_path)
    imdb = load_imdb(imdb_path)

    # Keep only columns we need
    cols = ["title", "genre", "description", "language", "duration",
            "episodes", "rating", "cast", "keywords", "source", "poster_url"]
    netflix = netflix[[c for c in cols if c in netflix.columns]]
    imdb = imdb[[c for c in cols if c in imdb.columns]]

    # Combine (IMDB first so richer data with posters/ratings/cast is kept on duplicates)
    combined = pd.concat([imdb, netflix], ignore_index=True)

    # Clean text fields
    text_cols = ["title", "genre", "description", "language", "cast", "keywords"]
    for col in text_cols:
        if col in combined.columns:
            combined[col] = combined[col].fillna("").astype(str).apply(clean_text)

    # Override IMDb's default language for known non-English Indian films.
    imdb_override_mask = (combined["source"] == "imdb") & (combined["title"].isin(IMDB_LANGUAGE_OVERRIDES))
    combined.loc[imdb_override_mask, "language"] = combined.loc[imdb_override_mask, "title"].map(IMDB_LANGUAGE_OVERRIDES)

    # Clean numeric fields
    combined["episodes"] = pd.to_numeric(combined["episodes"], errors="coerce").fillna(1).astype(int)
    combined["rating"] = pd.to_numeric(combined["rating"], errors="coerce")

    # Clean duration: keep numeric part if possible
    def extract_minutes(val):
        if pd.isna(val):
            return np.nan
        s = str(val).lower()
        m = re.search(r"(\d+)", s)
        return int(m.group(1)) if m else np.nan

    combined["duration"] = combined["duration"].apply(extract_minutes)

    # Remove rows with missing titles
    combined = combined[combined["title"].str.len() > 0]

    # Build combined_features column
    def build_features(row):
        parts = [
            row.get("genre", ""),
            row.get("language", ""),
            str(row.get("duration", "")),
            str(row.get("episodes", "")),
            row.get("keywords", ""),
            row.get("description", ""),
            row.get("cast", ""),
        ]
        return " ".join(str(p) for p in parts if p and p != "nan")

    combined["combined_features"] = combined.apply(build_features, axis=1)

    # Drop duplicate titles (prefer keeping first occurrence)
    combined = combined.drop_duplicates(subset=["title"], keep="first")

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined.to_csv(output_path, index=False)
    print(f"Processed dataset saved to {output_path}")
    print(f"Shape: {combined.shape}")
    print(f"Columns: {list(combined.columns)}")
    return combined


if __name__ == "__main__":
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    netflix_path = os.path.join(BASE, "data", "raw", "NetflixOriginals.xlsx")
    imdb_path = os.path.join(BASE, "data", "raw", "imdb_top_1000.xlsx")
    output_path = os.path.join(BASE, "data", "processed", "entertainment_data.csv")

    # Fallback to common absolute paths if raw folder doesn't exist
    if not os.path.exists(netflix_path):
        netflix_path = r"C:\Users\thaku\NetflixOriginals.xlsx"
    if not os.path.exists(imdb_path):
        imdb_path = r"C:\Users\thaku\imdb_top_1000.xlsx"

    preprocess_dataset(netflix_path, imdb_path, output_path)

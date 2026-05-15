# Smart Entertainment Recommendation System

A content-based recommendation system that suggests movies, TV shows, dramas, and anime using machine learning (TF-IDF + Cosine Similarity).

## Features
- Combine two real-world datasets: **Netflix Originals** and **IMDB Top 1000**
- Content-based recommendations using combined textual features (genre, language, duration, episodes, keywords, description, cast)
- Interactive **Streamlit UI** with title selection, top-N slider, and source filters
- Displays similarity scores, genre, rating, language, duration, episodes, and description for each recommendation

## Tech Stack
- Python, Pandas, NumPy
- scikit-learn (TF-IDF, Cosine Similarity)
- Streamlit (UI)
- openpyxl (Excel I/O)

## Project Structure
```
entertainment-recommender/
├── data/
│   └── processed/
│       └── entertainment_data.csv   # Combined & cleaned dataset
├── src/
│   ├── data_preprocessing.py        # Data loading, cleaning, feature engineering
│   └── recommendation_engine.py   # TF-IDF vectorizer + cosine similarity
├── app.py                           # Streamlit application
├── requirements.txt
└── README.md
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate the processed dataset (one-time)
```bash
python src/data_preprocessing.py
```
This reads `NetflixOriginals.xlsx` and `imdb_top_1000.xlsx`, cleans them, engineers features, and saves `data/processed/entertainment_data.csv`.

### 3. Run the Streamlit app
```bash
streamlit run app.py
```

## How It Works
1. **Feature Engineering** (`data_preprocessing.py`): Merges both datasets, normalizes columns, cleans text, and creates a `combined_features` string from genre, language, duration, episodes, keywords, description, and cast.
2. **Vectorization & Similarity** (`recommendation_engine.py`): Converts `combined_features` into TF-IDF vectors and computes pairwise cosine similarity.
3. **Recommendations**: Given a title, the engine finds the most similar items by cosine similarity and returns them ranked.

## Future Enhancements
- Mood-based recommendations
- Watch-time prediction
- Trending content analysis
- Poster display using APIs
- Hybrid recommendation system (collaborative + content-based)

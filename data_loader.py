# data_loader.py

import json, sys
from wordfreq import top_n_list
import spacy

from config import WORD_SOURCE, WORD_SOURCE_FILE, MAX_RAW_WORDS, BLACKLIST_FILE

# Carga modelo spaCy (en one-liner)
nlp = spacy.load("es_core_news_lg", disable=["parser","ner","lemmatizer"])

def load_blacklist() -> set[str]:
    try:
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {w.lower() for w in data} if isinstance(data, (list, set)) else set()
    except Exception:
        return set()

def get_raw_words() -> list[str]:
    if WORD_SOURCE == "wordfreq":
        return top_n_list("es", MAX_RAW_WORDS)
    try:
        with open(WORD_SOURCE_FILE, encoding="utf-8") as f:
            return [w.strip() for w in f if w.strip()]
    except FileNotFoundError:
        sys.exit(f"Error: no existe {WORD_SOURCE_FILE}")

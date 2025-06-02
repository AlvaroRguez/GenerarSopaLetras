# data_loader.py

import json
# import sys # sys.exit is no longer used
from wordfreq import top_n_list
import spacy

# Import default values from config with aliases
from config import (
    WORD_SOURCE as DEFAULT_WORD_SOURCE,
    WORD_SOURCE_FILE as DEFAULT_WORD_SOURCE_FILE,
    MAX_RAW_WORDS as DEFAULT_MAX_RAW_WORDS,
    BLACKLIST_FILE as DEFAULT_BLACKLIST_FILE
)

# Carga modelo spaCy (en one-liner)
# nlp = spacy.load("es_core_news_lg", disable=["parser","ner","lemmatizer"])
# This is not used in the provided functions. If it's used elsewhere in the actual project, keep it.
# For now, commenting out as per the functions being refactored. If other functions in this file use it, it should be uncommented.


def load_blacklist(blacklist_file_path: str = None) -> set[str]:
    files_to_try = []
    if blacklist_file_path:
        files_to_try.append(blacklist_file_path)
    files_to_try.append(DEFAULT_BLACKLIST_FILE) # Fallback

    for file_path in files_to_try:
        if not file_path:  # Skip if path is None or empty
            continue
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Ensure words are lowercase and handle potential non-list/set data
            return {str(w).lower() for w in data if isinstance(w, (str, int, float))} if isinstance(data, (list, set)) else set()
        except FileNotFoundError:
            print(f"Info: Blacklist file not found at {file_path}. Trying next option.")
            continue # Try the next file path
        except json.JSONDecodeError:
            print(f"Warning: Blacklist file {file_path} is not valid JSON. Skipping.")
            continue # Try the next file path
        except Exception as e:
            print(f"Warning: Could not load blacklist from {file_path} due to {e}. Trying next option.")
            continue # Try the next file path

    print("Info: No blacklist file loaded. Proceeding with an empty blacklist.")
    return set()


def get_raw_words(word_source_file_path: str = None,
                  word_source_type: str = None,
                  max_raw_words: int = None) -> list[str]:

    source_type_to_use = word_source_type if word_source_type else DEFAULT_WORD_SOURCE
    limit = max_raw_words if max_raw_words is not None else DEFAULT_MAX_RAW_WORDS

    if source_type_to_use == "file":
        file_to_load = word_source_file_path if word_source_file_path else DEFAULT_WORD_SOURCE_FILE
        if not file_to_load:
            # This case should ideally not happen if DEFAULT_WORD_SOURCE_FILE is always set in config
            # Or if word_source_file_path is guaranteed when type is "file" from form
            raise ValueError("Word source type is 'file' but no file path was provided or configured.")
        try:
            with open(file_to_load, encoding="utf-8") as f:
                # Apply limit if specified, otherwise read all words
                words = [w.strip() for w in f if w.strip()]
                return words[:limit] if limit is not None else words
        except FileNotFoundError:
            # Re-raise the error to be handled by the caller (e.g., the Flask app)
            raise FileNotFoundError(f"Error: Word source file not found at {file_to_load}")
        except Exception as e:
            # Handle other potential I/O errors
            print(f"Error reading word file {file_to_load}: {e}")
            return [] # Or raise a custom error

    elif source_type_to_use == "wordfreq":
        try:
            # Ensure limit is a positive integer for top_n_list
            if limit is None or limit <= 0:
                # wordfreq might have its own default or behavior for non-positive n,
                # but explicit handling is safer. Assuming a sensible default if limit is bad.
                effective_limit = DEFAULT_MAX_RAW_WORDS if DEFAULT_MAX_RAW_WORDS > 0 else 1000
            else:
                effective_limit = limit
            return top_n_list("es", effective_limit) # Assuming "es" (Spanish) is the target language
        except Exception as e:
            print(f"Error fetching words from wordfreq: {e}")
            return [] # Or raise a custom error

    else:
        print(f"Warning: Unknown word source type '{source_type_to_use}'. Returning empty list.")
        return []

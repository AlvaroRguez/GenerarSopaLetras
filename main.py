#!/usr/bin/env python3
"""
main.py: Orchestrates the generation of word‐search puzzles and exports to DOCX and PDF.
"""

import random
import os
from tqdm import tqdm

from config import (
    TOTAL_PUZZLES,
    WORDS_PER_PUZZLE,
    TQDM_NCOLS,
    WORD_SOURCE,
    WORD_SOURCE_FILE,
)
from data_loader import get_raw_words, load_blacklist
from generator import build_filtered_dict, generate_word_search
from export_docx import create_docx
from export_pdf import create_pdf


def main():
    # 1) Load and filter word list
    raw = get_raw_words()
    print(f"Retrieved {len(raw)} raw words.")
    blacklist = load_blacklist()
    filtered = build_filtered_dict(raw, blacklist)
    print(f"Filtered dictionary: {len(filtered)} words.\n")

    # 2) Save filtered dictionary for inspection
    out_file = f"{WORD_SOURCE}_{os.path.basename(WORD_SOURCE_FILE)}_filtered.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        for w in filtered:
            f.write(w + "\n")
    print(f"Filtered dictionary saved to '{out_file}'.\n")

    # 3) Generate puzzles
    all_puzzles = []
    used = set()
    for _ in tqdm(
        range(TOTAL_PUZZLES),
        desc="Generating puzzles",
        unit="puzzle",
        ncols=TQDM_NCOLS,
    ):
        # ensure we always have enough unique words
        avail = [w for w in filtered if w.upper() not in used]
        if len(avail) < WORDS_PER_PUZZLE:
            used.clear()
            avail = filtered.copy()

        selection = random.sample(avail, WORDS_PER_PUZZLE)
        used.update(w.upper() for w in selection)

        puzzle, locations = generate_word_search(selection)
        all_puzzles.append((puzzle, [w.upper() for w in selection], locations))

    print("\nPuzzle generation complete.\n")

    # 4) Export to DOCX and PDF
    print("Creating DOCX...")
    create_docx(all_puzzles)
    print("Creating PDF...")
    create_pdf(all_puzzles)
    print("All done!")


if __name__ == "__main__":
    main()

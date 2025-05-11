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
    TQDM_COLS,
    WORD_SOURCE,
    WORD_SOURCE_FILE,
    PUZZLE_ROWS,
    PUZZLE_COLUMNS,
    USE_LOOKFOR,
)
from data_loader import get_raw_words, load_blacklist
from generator import build_filtered_dict, generate_word_search
from export_docx import create_docx


def main():
    # 1) Load & filter
    raw = get_raw_words()
    tqdm.write(f"🔍 Retrieved {len(raw)} raw words.")
    blacklist = load_blacklist()
    filtered = build_filtered_dict(raw, blacklist)
    tqdm.write(f"✅ Filtered dictionary: {len(filtered)} words.\n")

    # 2) Dump filtered list for inspection
    out_file = f"{WORD_SOURCE}_{os.path.basename(WORD_SOURCE_FILE)}_filtered.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        for w in filtered:
            f.write(w + "\n")
    tqdm.write(f"📝 Filtered dictionary saved to '{out_file}'.\n")

    # 3) Generate puzzles
    all_puzzles = []
    used = set()
    for _ in tqdm(range(TOTAL_PUZZLES),
                  desc="Generating puzzles",
                  unit="puzzle",
                  ncols=TQDM_COLS):
        # ensure enough fresh words
        avail = [w for w in filtered if w.upper() not in used]
        if len(avail) < WORDS_PER_PUZZLE:
            used.clear()
            avail = filtered.copy()

        selection = random.sample(avail, WORDS_PER_PUZZLE)
        used.update(w.upper() for w in selection)

        # call generator with algorithm flags
        result = generate_word_search(
            selection,
            rows=PUZZLE_ROWS,
            columns=PUZZLE_COLUMNS,
            use_lookfor=USE_LOOKFOR
        )

        # flexible unpacking: (pzl, locs) or (pzl, words_placed, locs)
        if len(result) == 3:
            puzzle, placed_words, locations = result
        else:
            puzzle, locations = result
            placed_words = list(locations.keys())

        # warn if didn’t reach the target
        if len(placed_words) < WORDS_PER_PUZZLE:
            tqdm.write(f"⚠️  Only placed {len(placed_words)}/{WORDS_PER_PUZZLE} words in this puzzle.")

        all_puzzles.append((puzzle, placed_words, locations))

    tqdm.write("\n🎯 Puzzle generation complete.\n")

    # 4) Export
    tqdm.write("📄 Creating DOCX…")
    create_docx(all_puzzles)
    # La creación de PDF ahora se maneja dentro de create_docx
    # No es necesaria una llamada separada a create_pdf.
    tqdm.write("🏁 All done!")


if __name__ == "__main__":
    main()

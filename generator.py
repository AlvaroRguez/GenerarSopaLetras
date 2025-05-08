# generator.py

import random
import math
import spacy
from spacy.tokens import Doc

nlp = spacy.load('es_core_news_lg')
from config import (MIN_WORD_LENGTH, MAX_WORD_LENGTH, POS_ALLOWED,
                    WORDS_PER_PUZZLE, PUZZLE_ROWS, PUZZLE_COLUMNS,
                    MAX_FALLBACK_TRIES, ALPHABET, DIRECTIONS)

def build_filtered_dict(raw: list[str], blacklist: set[str]) -> list[str]:
    pre = [
        w for w in raw
        if MIN_WORD_LENGTH <= len(w) <= MAX_WORD_LENGTH
           and w.isascii() and w.isalpha()
           and w.lower() not in blacklist
    ]
    filtered = []
    for doc in nlp.pipe(pre, batch_size=2000, n_process=1):
        if doc[0].pos_ in POS_ALLOWED:
            filtered.append(doc[0].text)
    return filtered

def generate_word_search(
    words: list[str],
    rows: int = PUZZLE_ROWS,
    columns: int = PUZZLE_COLUMNS
) -> tuple[list[list[str]], dict[str,tuple[tuple[int,int],tuple[int,int]]]]:
    """Generates a word search puzzle using constants DIRECTIONS, ALPHABET, MAX_FALLBACK_TRIES..."""
    # 0) Sort from longest to shortest
    words = sorted(words, key=lambda w: -len(w))
    puzzle = [['' for _ in range(columns)] for _ in range(rows)]
    dir_counts = {d: 0 for d in DIRECTIONS}
    locations: dict[str, tuple[tuple[int,int], tuple[int,int]]] = {}

    for word in words:
        p = word.upper()
        candidates: list[tuple[int,int,int,int,int]] = []

        # 1) Explore valid positions
        for df, dc in DIRECTIONS:
            for r0 in range(rows):
                for c0 in range(columns):
                    rf = r0 + df*(len(p)-1)
                    cf = c0 + dc*(len(p)-1)
                    if not (0 <= rf < rows and 0 <= cf < columns):
                        continue
                    match_count = 0
                    ok = True
                    r, c = r0, c0
                    for l in p:
                        if puzzle[r][c] == l:
                            match_count += 1
                        elif puzzle[r][c] != '':
                            ok = False
                            break
                        r += df; c += dc
                    if ok:
                        candidates.append((match_count, r0, c0, df, dc))

        # 2) Choose best candidate (crossings + direction balancing)
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            max_match = candidates[0][0]
            top = [c for c in candidates if c[0] == max_match]
            top.sort(key=lambda x: dir_counts[(x[3], x[4])])
            _, r0, c0, df, dc = top[0]
            rf = r0 + df*(len(p)-1)
            cf = c0 + dc*(len(p)-1)
        else:
            # random fallback without mandatory crossing
            placed = False
            for _ in range(MAX_FALLBACK_TRIES):
                df, dc = random.choice(DIRECTIONS)
                r0, c0 = random.randrange(rows), random.randrange(columns)
                rf = r0 + df*(len(p)-1)
                cf = c0 + dc*(len(p)-1)
                if not (0 <= rf < rows and 0 <= cf < columns):
                    continue
                ok = True
                r, c = r0, c0
                for l in p:
                    if puzzle[r][c] not in ('', l):
                        ok = False
                        break
                    r += df; c += dc
                if ok:
                    placed = True
                    break
            if not placed:
                continue

        # 3) Place the word and update direction counter
        r, c = r0, c0
        for l in p:
            puzzle[r][c] = l
            r += df; c += dc
        locations[p] = ((r0, c0), (rf, cf))
        dir_counts[(df, dc)] += 1

    # 4) Fill empty spaces
    for i in range(rows):
        for j in range(columns):
            if puzzle[i][j] == '':
                puzzle[i][j] = random.choice(ALPHABET)

    return puzzle, locations

# generator.py

import spacy

nlp = spacy.load('es_core_news_lg')
from config import (MIN_WORD_LENGTH, MAX_WORD_LENGTH, POS_ALLOWED, DIRECTIONS, MAX_FALLBACK_TRIES,
                    PUZZLE_ROWS, PUZZLE_COLUMNS, WORDS_PER_PUZZLE, USE_LOOKFOR)

# Importamos las funciones de los módulos refactorizados
from greedy import greedy_word_search
from placement_utils import try_random_placement
from word_placement import fill_empty_spaces
from lookfor import lookfor_sequential_word_search

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
    columns: int = PUZZLE_COLUMNS,
    use_lookfor: bool = USE_LOOKFOR
) -> tuple[list[list[str]], list[str], dict[str, tuple[tuple[int, int], tuple[int, int]]]]:
    words = sorted(words, key=lambda w: -len(w))
    placed: list[str] # Type hint for placed, assigned in branches
    # 1) Generación inicial
    if use_lookfor:
        puzzle, placed, locations = lookfor_sequential_word_search(words, rows, columns)
    else:   
        puzzle, locations = greedy_word_search(words, rows, columns)
        placed = list(locations.keys()) # Define placed for this branch

    # 2) Asegurar siempre WORDS_PER_PUZZLE
    current = len(locations)
    if current < WORDS_PER_PUZZLE:
        # reconstruimos dir_counts de lo ya colocado
        dir_counts = {d:0 for d in DIRECTIONS}
        for ((r0,c0),(rf,cf)) in locations.values():
            d = ( (rf>r0)-(rf<r0), (cf>c0)-(cf<c0) )
            dir_counts[d] += 1
        # intentamos colocar las palabras que faltan
        for w in words:
            if len(locations) >= WORDS_PER_PUZZLE:
                break
            if w.upper() in locations:
                continue
            success = try_random_placement(
                w, puzzle, rows, columns,
                locations, dir_counts,
                max_tries=MAX_FALLBACK_TRIES
            )
            if success:
                # actualizamos dir_counts
                loc = locations[w.upper()]
                d = ( (loc[1][0]>loc[0][0]) - (loc[1][0]<loc[0][0]),
                      (loc[1][1]>loc[0][1]) - (loc[1][1]<loc[0][1]) )
                dir_counts[d] += 1

    # 3) Relleno final
    fill_empty_spaces(puzzle, rows, columns)
    return puzzle, placed, locations
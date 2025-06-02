# generator.py

import spacy

nlp = spacy.load('es_core_news_lg')

# Import default values from config with aliases
from config import (
    MIN_WORD_LENGTH as DEFAULT_MIN_WORD_LENGTH,
    MAX_WORD_LENGTH as DEFAULT_MAX_WORD_LENGTH,
    POS_ALLOWED as DEFAULT_POS_ALLOWED,
    DIRECTIONS as DEFAULT_DIRECTIONS,
    MAX_FALLBACK_TRIES as DEFAULT_MAX_FALLBACK_TRIES,
    WORDS_PER_PUZZLE as DEFAULT_WORDS_PER_PUZZLE
    # PUZZLE_ROWS, PUZZLE_COLUMNS, USE_LOOKFOR are removed as per instructions,
    # assuming app.py will always provide these values for generate_word_search
)

# Importamos las funciones de los módulos refactorizados
from greedy import greedy_word_search
from placement_utils import try_random_placement
from word_placement import fill_empty_spaces
from lookfor import lookfor_sequential_word_search

def build_filtered_dict(raw: list[str],
                        blacklist: set[str],
                        min_word_length: int = None,
                        max_word_length: int = None,
                        pos_allowed: set[str] = None) -> list[str]:

    min_len = min_word_length if min_word_length is not None else DEFAULT_MIN_WORD_LENGTH
    max_len = max_word_length if max_word_length is not None else DEFAULT_MAX_WORD_LENGTH
    pos_tags = pos_allowed if pos_allowed is not None else DEFAULT_POS_ALLOWED

    pre = [
        w for w in raw
        if min_len <= len(w) <= max_len
           and w.isascii() and w.isalpha()
           and w.lower() not in blacklist
    ]
    filtered = []
    # Consider adding a check if not pre: return [] to avoid nlp.pipe with empty list
    if not pre:
        return []
    for doc in nlp.pipe(pre, batch_size=2000, n_process=1): # n_process might be better as -1 or configurable
        if doc and doc[0].pos_ in pos_tags: # Check if doc is not empty
            filtered.append(doc[0].text)
    return filtered

def generate_word_search(
    words: list[str],
    rows: int, # PUZZLE_ROWS default removed
    columns: int, # PUZZLE_COLUMNS default removed
    words_per_puzzle_target: int, # New parameter
    use_lookfor: bool, # USE_LOOKFOR default removed
    directions: list[tuple[int,int]] = None,
    max_fallback_tries: int = None
) -> tuple[list[list[str]], list[str], dict[str, tuple[tuple[int, int], tuple[int, int]]]]:

    actual_directions = directions if directions is not None else DEFAULT_DIRECTIONS
    actual_max_fallback_tries = max_fallback_tries if max_fallback_tries is not None else DEFAULT_MAX_FALLBACK_TRIES
    actual_words_per_puzzle_target = words_per_puzzle_target if words_per_puzzle_target is not None else DEFAULT_WORDS_PER_PUZZLE

    words = sorted(words, key=lambda w: -len(w))
    placed: list[str] # Type hint for placed, assigned in branches
    locations: dict[str, tuple[tuple[int, int], tuple[int, int]]] # Ensure locations is typed

    # 1) Generación inicial
    if use_lookfor:
        # Assuming lookfor_sequential_word_search also uses actual_directions if it uses directions
        puzzle, placed, locations = lookfor_sequential_word_search(words, rows, columns, actual_directions)
    else:   
        # Assuming greedy_word_search also uses actual_directions
        puzzle, locations = greedy_word_search(words, rows, columns, actual_directions)
        placed = list(locations.keys()) # Define placed for this branch

    # 2) Asegurar siempre words_per_puzzle_target
    current_placed_count = len(locations)
    if current_placed_count < actual_words_per_puzzle_target:
        # reconstruimos dir_counts de lo ya colocado
        dir_counts = {d:0 for d in actual_directions} # Use actual_directions
        for ((r0,c0),(rf,cf)) in locations.values():
            # Ensure robust calculation of direction vector d
            dr = (rf > r0) - (rf < r0)
            dc = (cf > c0) - (cf < c0)
            d = (dr, dc)
            if d in dir_counts: # Check if direction is valid/expected
                dir_counts[d] += 1
            else:
                # This case should ideally not happen if locations are generated correctly by placement functions
                print(f"Warning: Unexpected direction vector {d} calculated for a placed word.")


        # intentamos colocar las palabras que faltan
        for w in words: # Iterate through the original sorted list of candidate words
            if len(locations) >= actual_words_per_puzzle_target:
                break # Stop if we've met the target

            # Check if word (or its uppercase version, as keys in locations are upper) is already placed
            # This check might be redundant if `words` list is pre-filtered or `try_random_placement` handles it
            if w.upper() in locations:
                continue

            success = try_random_placement(
                w, puzzle, rows, columns,
                locations, dir_counts, # dir_counts is based on actual_directions
                max_tries=actual_max_fallback_tries, # Use actual_max_fallback_tries
                directions_to_try=actual_directions # Pass actual_directions to try_random_placement
            )
            if success:
                # actualizamos dir_counts (if try_random_placement doesn't do it internally)
                # This part of the logic assumes try_random_placement updates locations and returns True
                # And that the direction calculation here is consistent
                # It's often better if try_random_placement returns the direction used or updates dir_counts itself.
                newly_placed_word_key = w.upper() # Assuming key is uppercase
                if newly_placed_word_key in locations:
                    loc = locations[newly_placed_word_key]
                    dr_new = (loc[1][0] > loc[0][0]) - (loc[1][0] < loc[0][0])
                    dc_new = (loc[1][1] > loc[0][1]) - (loc[1][1] < loc[0][1])
                    d_new = (dr_new, dc_new)
                    if d_new in dir_counts:
                        dir_counts[d_new] += 1
                    else:
                        print(f"Warning: Unexpected direction vector {d_new} for newly placed word {w}.")
                else:
                    # This would indicate an issue with try_random_placement not updating locations as expected
                    print(f"Warning: Word {w} reported as successfully placed but not found in locations dict.")

        # Update `placed` list after attempting to add more words
        placed = list(locations.keys())


    # 3) Relleno final
    fill_empty_spaces(puzzle, rows, columns)
    return puzzle, placed, locations
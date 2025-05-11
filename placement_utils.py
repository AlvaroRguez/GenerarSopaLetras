# placement_utils.py
import random
from config import DIRECTIONS, MAX_FALLBACK_TRIES
from word_placement import place_word

def _try_primary_placement(
    word_upper: str, puzzle: list[list[str]], rows: int, columns: int,
    locations: dict, dir_counts: dict, sorted_directions: list[tuple[int,int]],
    is_short_word: bool, primary_tries: int
) -> bool:
    """Intenta la colocación primaria (estratégica)."""
    for _ in range(primary_tries):
        df, dc = sorted_directions[min(random.randint(0, len(sorted_directions)-1),
                                      random.randint(0, len(sorted_directions)-1))]
        
        if is_short_word:
            center_r, center_c = rows//2, columns//2
            r_offset = int(random.gauss(0, rows//4))
            c_offset = int(random.gauss(0, columns//4))
            r0 = max(0, min(rows-1, center_r + r_offset))
            c0 = max(0, min(columns-1, center_c + c_offset))
        else:
            r0, c0 = random.randrange(rows), random.randrange(columns)
            
        rf = r0 + df*(len(word_upper)-1)
        cf = c0 + dc*(len(word_upper)-1)
        
        if not (0 <= rf < rows and 0 <= cf < columns):
            continue
            
        ok = True
        r, c = r0, c0
        for l_char in word_upper:
            if puzzle[r][c] not in ('', l_char):
                ok = False
                break
            r += df; c += dc
            
        if ok:
            loc = place_word(word_upper, puzzle, r0, c0, df, dc)
            locations[word_upper] = loc
            dir_counts[(df, dc)] = dir_counts.get((df,dc), 0) + 1
            return True
    return False

def _try_secondary_placement(
    word_upper: str, puzzle: list[list[str]], rows: int, columns: int,
    locations: dict, dir_counts: dict, secondary_tries: int
) -> bool:
    """Intenta la colocación secundaria (completamente aleatoria)."""
    for _ in range(secondary_tries):
        df, dc = random.choice(DIRECTIONS)
        r0, c0 = random.randrange(rows), random.randrange(columns)
        rf = r0 + df*(len(word_upper)-1)
        cf = c0 + dc*(len(word_upper)-1)
        
        if not (0 <= rf < rows and 0 <= cf < columns):
            continue
            
        ok = True
        r, c = r0, c0
        for l_char in word_upper:
            if puzzle[r][c] not in ('', l_char):
                ok = False
                break
            r += df; c += dc
            
        if ok:
            loc = place_word(word_upper, puzzle, r0, c0, df, dc)
            locations[word_upper] = loc
            dir_counts[(df, dc)] = dir_counts.get((df,dc), 0) + 1
            return True
    return False

def try_random_placement(word: str, puzzle: list[list[str]], rows: int, columns: int, 
                        locations: dict, dir_counts: dict, max_tries: int = None) -> bool:
    """Try to place a word in a random position.
    Returns True if successful, False otherwise."""
    max_tries = max_tries or MAX_FALLBACK_TRIES
    p = word.upper()
    
    is_short_word = len(p) <= 5
    sorted_directions = sorted(DIRECTIONS, key=lambda d: dir_counts.get(d, 0))
    
    primary_tries_ratio = 0.7
    if is_short_word:
        primary_tries_ratio = 0.8

    primary_tries = int(max_tries * primary_tries_ratio)
    secondary_tries = max_tries - primary_tries
    
    if _try_primary_placement(p, puzzle, rows, columns, locations, dir_counts, sorted_directions, is_short_word, primary_tries):
        return True
    
    if _try_secondary_placement(p, puzzle, rows, columns, locations, dir_counts, secondary_tries):
        return True
    
    return False
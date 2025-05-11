# greedy_utils.py
import random
from config import MAX_FALLBACK_TRIES

def _explore_candidates(
    word_upper: str,
    puzzle: list[list[str]],
    rows: int,
    columns: int,
    random_directions: list[tuple[int, int]],
    dir_counts: dict[tuple[int, int], int]
) -> tuple[int, int, int, int, int] | None:
    """Explora posiciones válidas y elige el mejor candidato."""
    candidates: list[tuple[int, int, int, int, int]] = []
    for df, dc in random_directions:
        for r0 in range(rows):
            for c0 in range(columns):
                rf = r0 + df * (len(word_upper) - 1)
                cf = c0 + dc * (len(word_upper) - 1)
                if not (0 <= rf < rows and 0 <= cf < columns):
                    continue
                match_count = 0
                ok = True
                r, c = r0, c0
                for char_in_word in word_upper:
                    if puzzle[r][c] == char_in_word:
                        match_count += 1
                    elif puzzle[r][c] != '':
                        ok = False
                        break
                    r += df
                    c += dc
                if ok:
                    candidates.append((match_count, r0, c0, df, dc))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        max_match = candidates[0][0]
        top = [c for c in candidates if c[0] == max_match]
        top.sort(key=lambda x: dir_counts.get((x[3], x[4]), 0))
        return top[0]
    return None

def _fallback_placement(
    word_upper: str,
    puzzle: list[list[str]],
    rows: int,
    columns: int,
    random_directions: list[tuple[int, int]]
) -> tuple[int, int, int, int] | None:
    """Intenta colocar la palabra aleatoriamente si no hay candidatos con cruces."""
    for _ in range(MAX_FALLBACK_TRIES):
        df, dc = random.choice(random_directions)
        r0, c0 = random.randrange(rows), random.randrange(columns)
        rf = r0 + df * (len(word_upper) - 1)
        cf = c0 + dc * (len(word_upper) - 1)
        if not (0 <= rf < rows and 0 <= cf < columns):
            continue
        ok = True
        r, c = r0, c0
        for char_in_word in word_upper:
            if puzzle[r][c] not in ('', char_in_word):
                ok = False
                break
            r += df
            c += dc
        if ok:
            return r0, c0, df, dc
    return None
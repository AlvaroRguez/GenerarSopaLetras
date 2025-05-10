# greedy.py

import random
from config import DIRECTIONS, PUZZLE_ROWS, PUZZLE_COLUMNS, MAX_FALLBACK_TRIES
from word_placement import fill_empty_spaces
from tqdm import tqdm

def greedy_word_search(
    words: list[str],
    rows: int = PUZZLE_ROWS,
    columns: int = PUZZLE_COLUMNS
) -> tuple[list[list[str]], dict[str,tuple[tuple[int,int],tuple[int,int]]]]:
    """Algoritmo greedy para generación de sopas de letras.
    Garantiza que se coloquen exactamente WORDS_PER_PUZZLE palabras (o todas si hay menos)."""
    from config import WORDS_PER_PUZZLE
    from backtracking_utils import create_fallback_solution
    
    # Ordenar palabras por longitud (más largas primero) para mejorar la colocación
    words = sorted(words, key=lambda w: -len(w))
    target_words = min(WORDS_PER_PUZZLE, len(words))
    
    # Intentar múltiples veces hasta colocar suficientes palabras
    max_attempts = 3
    best_puzzle = None
    best_locations = {}
    
    for attempt in range(max_attempts):
        puzzle = [['' for _ in range(columns)] for _ in range(rows)]
        dir_counts = {d: 0 for d in DIRECTIONS}
        locations: dict[str, tuple[tuple[int,int], tuple[int,int]]] = {}
        
        # Mezclar direcciones para cada intento
        random_directions = list(DIRECTIONS)
        if attempt > 0:
            random.shuffle(random_directions)

        for word in words:
            # Si ya colocamos suficientes palabras, terminamos
            if len(locations) >= target_words:
                break
                
            p = word.upper()
            candidates: list[tuple[int,int,int,int,int]] = []

            # 1) Explore valid positions
            for df, dc in random_directions:
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
                    df, dc = random.choice(random_directions)
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
        
        # Guardar el mejor resultado hasta ahora
        if len(locations) > len(best_locations):
            best_puzzle = [row[:] for row in puzzle]  # Deep copy
            best_locations = locations.copy()
            
        # Si ya tenemos suficientes palabras, terminamos
        if len(best_locations) >= target_words:
            break
    
    # Si no se colocaron suficientes palabras, usar solución de fallback
    if best_puzzle is None or len(best_locations) < target_words:
        tqdm.write(f"Usando solución de fallback en greedy para colocar {target_words} palabras")
        return create_fallback_solution(words, rows, columns)

    # 4) Fill empty spaces
    fill_empty_spaces(best_puzzle, rows, columns)

    return best_puzzle, best_locations
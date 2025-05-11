# greedy.py

import random
from config import DIRECTIONS, PUZZLE_ROWS, PUZZLE_COLUMNS, MAX_FALLBACK_TRIES, WORDS_PER_PUZZLE
from word_placement import fill_empty_spaces
from greedy_utils import _explore_candidates, _fallback_placement


def greedy_word_search(
    words: list[str],
    rows: int = PUZZLE_ROWS,
    columns: int = PUZZLE_COLUMNS
) -> tuple[list[list[str]], dict[str,tuple[tuple[int,int],tuple[int,int]]]]:
    """Algoritmo greedy para generación de sopas de letras.
    Garantiza que se coloquen exactamente WORDS_PER_PUZZLE palabras (o todas si hay menos)."""
        
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

            best_candidate_info = _explore_candidates(p, puzzle, rows, columns, random_directions, dir_counts)

            if best_candidate_info:
                _, r0, c0, df, dc = best_candidate_info
            else:
                fallback_info = _fallback_placement(p, puzzle, rows, columns, random_directions)
                if fallback_info:
                    r0, c0, df, dc = fallback_info
                else:
                    continue  # No se pudo colocar la palabra
            
            # 3) Place the word and update direction counter
            r, c = r0, c0
            for l_char in p:
                puzzle[r][c] = l_char
                r += df; c += dc
            locations[p] = ((r0, c0), (r0 + df*(len(p)-1), c0 + dc*(len(p)-1)))
            dir_counts[(df, dc)] += 1
        
        # Guardar el mejor resultado hasta ahora
        if len(locations) > len(best_locations):
            best_puzzle = [row[:] for row in puzzle]  # Deep copy
            best_locations = locations.copy()
            
        # Si ya tenemos suficientes palabras, terminamos
        if len(best_locations) >= target_words:
            break
    
    # 4) Fill empty spaces
    fill_empty_spaces(best_puzzle, rows, columns)

    return best_puzzle, best_locations
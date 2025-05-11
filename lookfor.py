# lookfor_sequential_word_search.py

import random
import time
from typing import List, Tuple, Dict
from tqdm import tqdm

from config import (
    WORDS_PER_PUZZLE,
    PUZZLE_ROWS, PUZZLE_COLUMNS,
    DIRECTIONS, ALPHABET, VERBOSE
)

def lookfor_sequential_word_search(
    words: List[str],
    rows: int = PUZZLE_ROWS,
    cols: int = PUZZLE_COLUMNS
) -> Tuple[List[List[str]], List[str], Dict[str, Tuple[Tuple[int,int],Tuple[int,int]]]]:
    """
    Coloca secuencialmente WORDS_PER_PUZZLE palabras, tratando de maximizar cruces
    y equilibrar el uso de direcciones.
    Devuelve: (tablero, lista_de_palabras_colocadas, ubicaciones)
    """
    start_all = time.perf_counter()

    # 1) Matriz vacía
    puzzle = [['' for _ in range(cols)] for _ in range(rows)]
    locations: Dict[str, Tuple[Tuple[int,int],Tuple[int,int]]] = {}
    placed_words: List[str] = []

    # 2) Conteo de uso de cada dirección
    dir_counts = {d: 0 for d in DIRECTIONS}

    if VERBOSE:
       tqdm.write(f"\n[LOOKFOR] Generando sopa secuencial ({rows}×{cols}), "
              f"{len(words)} candidatas, colocando {WORDS_PER_PUZZLE}...\n")

    placed = 0
    for word in words:
        if placed >= WORDS_PER_PUZZLE:
            break

        p = word.upper()
        L = len(p)
        candidates: List[Tuple[int,int,int,int,int]] = []

        # 3) Explorar todas las posiciones posibles
        for df, dc in DIRECTIONS:
            for r0 in range(rows):
                for c0 in range(cols):
                    rf = r0 + df*(L-1)
                    cf = c0 + dc*(L-1)
                    if not (0 <= rf < rows and 0 <= cf < cols):
                        continue

                    match = 0
                    ok = True
                    r, c = r0, c0
                    for ch in p:
                        if puzzle[r][c] == ch:
                            match += 1
                        elif puzzle[r][c] != '':
                            ok = False
                            break
                        r += df; c += dc

                    if ok:
                        candidates.append((match, r0, c0, df, dc))

        if not candidates:
            if VERBOSE:
               tqdm.write(f" [SKIP] '{word}' no cabe en ningún lugar.")
            continue

        # 4) Filtrar: primero por más cruces, luego por dirección menos usada
        candidates.sort(key=lambda x: x[0], reverse=True)
        max_match = candidates[0][0]
        top = [c for c in candidates if c[0] == max_match]
        top.sort(key=lambda x: dir_counts[(x[3], x[4])])

        match, r0, c0, df, dc = top[0]
        rf = r0 + df*(L-1)
        cf = c0 + dc*(L-1)

        # 5) Colocar la palabra
        r, c = r0, c0
        for ch in p:
            puzzle[r][c] = ch
            r += df; c += dc

        locations[p] = ((r0, c0), (rf, cf))
        dir_counts[(df, dc)] += 1
        placed += 1
        placed_words.append(word)

        if VERBOSE:
           tqdm.write(f" [{placed}/{WORDS_PER_PUZZLE}] Colocado '{word}' "
                  f"en {(r0,c0)} dir {(df,dc)} cruces={match}.")

    # 6) Rellenar espacios vacíos
    for i in range(rows):
        for j in range(cols):
            if puzzle[i][j] == '':
                puzzle[i][j] = random.choice(ALPHABET)

    if VERBOSE:
        total_time = time.perf_counter() - start_all
        tqdm.write(f"\n[LOOKFOR] Colocadas {placed}/{WORDS_PER_PUZZLE} palabras " f"en {total_time:.2f}s.")
        tqdm.write(" [LOOKFOR] Uso de direcciones:")
        for d, cnt in dir_counts.items():
            tqdm.write(f"   {d}: {cnt}")

    return puzzle, placed_words, locations

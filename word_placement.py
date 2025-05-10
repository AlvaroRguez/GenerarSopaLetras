# word_placement.py

import random
from config import DIRECTIONS, ALPHABET, MAX_FALLBACK_TRIES

def find_candidates(word: str, puzzle: list[list[str]], rows: int, columns: int, dir_counts: dict) -> list[tuple]:
    """Find all valid positions for a word in the current puzzle state.
    Returns a list of tuples (match_count, r0, c0, df, dc, quality_score)."""
    p = word.upper()
    candidates: list[tuple] = []
    
    # Calcular el centro del puzzle para priorizar posiciones centrales
    center_r, center_c = rows // 2, columns // 2
    
    # Ordenar direcciones por menos utilizadas primero para mejorar distribución
    sorted_directions = sorted(DIRECTIONS, key=lambda d: dir_counts.get(d, 0))
    
    # Explore valid positions with strategic prioritization
    for df, dc in sorted_directions:
        # Factor de prioridad para esta dirección (favorece direcciones menos usadas)
        dir_priority = 1.0 - (dir_counts.get((df, dc), 0) / (sum(dir_counts.values()) + 1))
        
        for r0 in range(rows):
            for c0 in range(columns):
                rf = r0 + df*(len(p)-1)
                cf = c0 + dc*(len(p)-1)
                if not (0 <= rf < rows and 0 <= cf < columns):
                    continue
                    
                # Verificar si la palabra cabe y contar coincidencias e intersecciones
                match_count = 0
                intersections = 0
                adjacent_letters = 0
                ok = True
                r, c = r0, c0
                
                for i, l in enumerate(p):
                    # Verificar si la celda actual es válida
                    if puzzle[r][c] == l:
                        match_count += 1
                        intersections += 1
                    elif puzzle[r][c] != '':
                        ok = False
                        break
                    
                    # Verificar celdas adyacentes (para detectar palabras cercanas)
                    for dr, dc2 in [(0,1), (1,0), (0,-1), (-1,0)]:
                        if (dr, dc2) == (df, dc) or (dr, dc2) == (-df, -dc):
                            continue  # Ignorar la dirección de la palabra
                        
                        nr, nc = r + dr, c + dc2
                        if 0 <= nr < rows and 0 <= nc < columns and puzzle[nr][nc] != '':
                            adjacent_letters += 1
                    
                    # Avanzar a la siguiente letra
                    r += df
                    c += dc
                
                if ok:
                    # Calcular distancia al centro (normalizada)
                    mid_r = r0 + df*(len(p)//2)
                    mid_c = c0 + dc*(len(p)//2)
                    center_dist = ((mid_r - center_r)**2 + (mid_c - center_c)**2)**0.5
                    max_dist = ((rows//2)**2 + (columns//2)**2)**0.5
                    center_factor = 1.0 - (center_dist / max_dist)
                    
                    # Calcular puntuación de calidad para este candidato
                    # Factores considerados:
                    # 1. Número de coincidencias (match_count)
                    # 2. Número de intersecciones (intersections)
                    # 3. Cercanía al centro (center_factor)
                    # 4. Prioridad de dirección (dir_priority)
                    # 5. Letras adyacentes (adjacent_letters)
                    quality_score = (
                        match_count * 10 +           # Priorizar coincidencias
                        intersections * 15 +         # Aumentar peso para intersecciones (calidad de cruces)
                        center_factor * 3 +          # Priorizar posiciones centrales
                        dir_priority * 2 +           # Priorizar direcciones menos usadas
                        min(adjacent_letters, 8) * 2 # Aumentar peso para letras adyacentes (densidad), con límite mayor
                    )
                    
                    candidates.append((match_count, r0, c0, df, dc, quality_score))
    
    # Ordenar candidatos por puntuación de calidad (mayor primero)
    return sorted(candidates, key=lambda x: x[5], reverse=True)
    
    return candidates

def place_word(word: str, puzzle: list[list[str]], r0: int, c0: int, df: int, dc: int) -> tuple[tuple[int,int], tuple[int,int]]:
    """Place a word in the puzzle and return its start and end coordinates."""
    p = word.upper()
    r, c = r0, c0
    rf = r0 + df*(len(p)-1)
    cf = c0 + dc*(len(p)-1)
    
    for l in p:
        puzzle[r][c] = l
        r += df; c += dc
        
    return ((r0, c0), (rf, cf))

def remove_word(word: str, puzzle: list[list[str]], r0: int, c0: int, df: int, dc: int) -> None:
    """Remove a word from the puzzle, preserving crossings with other words."""
    p = word.upper()
    r, c = r0, c0
    rows = len(puzzle)
    cols = len(puzzle[0]) if rows > 0 else 0
    
    for l in p:
        # Verificar que los índices estén dentro de los límites válidos
        if not (0 <= r < rows and 0 <= c < cols):
            break  # Salir del bucle si los índices están fuera de rango
            
        # Check if this cell is part of another word's crossing
        is_crossing = False
        for dr, dc2 in DIRECTIONS:
            if (dr, dc2) == (df, dc):
                continue  # Skip the direction of the word we're removing
            
            # Check in all other directions if there's a letter
            nr, nc = r - dr, c - dc2
            if 0 <= nr < rows and 0 <= nc < cols and puzzle[nr][nc] != '':
                is_crossing = True
                break
                
            nr, nc = r + dr, c + dc2
            if 0 <= nr < rows and 0 <= nc < cols and puzzle[nr][nc] != '':
                is_crossing = True
                break
        
        if not is_crossing:
            puzzle[r][c] = ''  # Only clear if not a crossing
        
        r += df; c += dc

def fill_empty_spaces(puzzle: list[list[str]], rows: int, columns: int) -> None:
    """Fill empty spaces in the puzzle with random letters."""
    for i in range(rows):
        for j in range(columns):
            if puzzle[i][j] == '':
                puzzle[i][j] = random.choice(ALPHABET)
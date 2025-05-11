# candidate_generation_utils.py
from config import DIRECTIONS

def _calculate_quality_score(
    match_count: int, intersections: int, center_factor: float,
    dir_priority: float, adjacent_letters: int
) -> float:
    """Calcula la puntuación de calidad para un candidato."""
    return (
        match_count * 10 +
        intersections * 15 +
        center_factor * 3 +
        dir_priority * 2 +
        min(adjacent_letters, 8) * 2
    )

def _check_candidate_position(
    p_word: str, r0: int, c0: int, df: int, dc: int, 
    puzzle: list[list[str]], rows: int, columns: int
) -> tuple[bool, int, int, int]:
    """Verifica si una palabra cabe en una posición y cuenta coincidencias/intersecciones."""
    rf = r0 + df * (len(p_word) - 1)
    cf = c0 + dc * (len(p_word) - 1)
    if not (0 <= rf < rows and 0 <= cf < columns):
        return False, 0, 0, 0

    match_count = 0
    intersections = 0
    adjacent_letters = 0
    ok = True
    r, c = r0, c0

    for char_in_word in p_word:
        if puzzle[r][c] == char_in_word:
            match_count += 1
            intersections += 1
        elif puzzle[r][c] != '':
            ok = False
            break
        
        # Verificar celdas adyacentes (para detectar palabras cercanas)
        for dr_adj, dc_adj in [(0,1), (1,0), (0,-1), (-1,0)]:
            if (dr_adj, dc_adj) == (df, dc) or (dr_adj, dc_adj) == (-df, -dc):
                continue  # Ignorar la dirección de la palabra
            
            nr, nc = r + dr_adj, c + dc_adj
            if 0 <= nr < rows and 0 <= nc < columns and puzzle[nr][nc] != '':
                adjacent_letters += 1
        
        r += df
        c += dc
    
    return ok, match_count, intersections, adjacent_letters

def find_candidates(word: str, puzzle: list[list[str]], rows: int, columns: int, dir_counts: dict) -> list[tuple]:
    """Find all valid positions for a word in the current puzzle state.
    Returns a list of tuples (match_count, r0, c0, df, dc, quality_score)."""
    p = word.upper()
    candidates: list[tuple] = []
    
    center_r, center_c = rows // 2, columns // 2
    sum_dir_counts = sum(dir_counts.values())
    if sum_dir_counts == 0:
        sum_dir_counts = 1 
        
    sorted_directions = sorted(DIRECTIONS, key=lambda d: dir_counts.get(d, 0))
    
    for df, dc in sorted_directions:
        dir_priority = 1.0 - (dir_counts.get((df, dc), 0) / sum_dir_counts)
        
        for r0 in range(rows):
            for c0 in range(columns):
                ok, match_count, intersections, adjacent_letters = _check_candidate_position(
                    p, r0, c0, df, dc, puzzle, rows, columns
                )
                                
                if ok:
                    mid_r = r0 + df*(len(p)//2)
                    mid_c = c0 + dc*(len(p)//2)
                    center_dist = ((mid_r - center_r)**2 + (mid_c - center_c)**2)**0.5
                    max_dist = ((rows//2)**2 + (columns//2)**2)**0.5
                    center_factor = 1.0 - (center_dist / max_dist if max_dist > 0 else 0)
                    
                    quality_score = _calculate_quality_score(
                        match_count, intersections, center_factor, 
                        dir_priority, adjacent_letters
                    )
                    
                    candidates.append((match_count, r0, c0, df, dc, quality_score))
    
    return sorted(candidates, key=lambda x: x[5], reverse=True)
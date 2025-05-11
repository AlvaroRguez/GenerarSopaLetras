# evaluation.py

from config import DIRECTIONS, WORDS_PER_PUZZLE

def _calculate_words_score(words_placed: int, locations: dict, target_words_count: int) -> float:
    """Calculates the score based on the number of words placed."""
    words_score = float(words_placed * 200)  # Aumentado significativamente
    
    actual_target_for_bonus = target_words_count
    if locations:
        actual_target_for_bonus = min(target_words_count, len(locations.keys()))

    if words_placed == actual_target_for_bonus and words_placed > 0:
        words_score += 3000  # Bonus muy alto por tener exactamente el número requerido
    elif words_placed >= actual_target_for_bonus * 0.9 and words_placed > 0:
        words_score += 1000  # Bonus por estar cerca del objetivo
    return words_score

def _calculate_cell_metrics(puzzle: list[list[str]], locations: dict) -> tuple[int, int, float]:
    """Calculates crossings, filled cells, and density."""
    crossings = 0
    filled_cells = 0
    cell_usage: dict[tuple[int, int], int] = {}
    
    for word, ((r0, c0), (rf, cf)) in locations.items():
        dr = 1 if rf > r0 else (-1 if rf < r0 else 0)
        dc = 1 if cf > c0 else (-1 if cf < c0 else 0)
        r, c = r0, c0
        for _ in range(len(word)):
            cell_usage[(r, c)] = cell_usage.get((r, c), 0) + 1
            r += dr
            c += dc
            
    for _cell, count in cell_usage.items():
        filled_cells += 1
        if count > 1:
            crossings += count - 1
            
    density = 0.0
    if puzzle and len(puzzle) > 0 and len(puzzle[0]) > 0:
        density = filled_cells / (len(puzzle) * len(puzzle[0]))
    return crossings, filled_cells, density

def _calculate_density_bonus(density: float) -> float:
    """Calculates bonus score based on puzzle density."""
    density_score = 0.0
    if 0.4 <= density <= 0.7:
        density_score = 500.0
    elif 0.3 <= density < 0.4 or 0.7 < density <= 0.8:
        density_score = 200.0
    return density_score

def _calculate_direction_balance_score(locations: dict, directions_config: list) -> float:
    """Calculates score based on balance of word directions."""
    dir_usage = {d: 0 for d in directions_config}
    for _, ((r0, c0), (rf, cf)) in locations.items():
        dr_actual = (rf > r0) - (rf < r0)
        dc_actual = (cf > c0) - (cf < c0)
        dir_key = (dr_actual, dc_actual)
        if dir_key in dir_usage:
            dir_usage[dir_key] += 1
            
    direction_balance = 0.0
    num_dirs_used = sum(1 for count in dir_usage.values() if count > 0)
    if num_dirs_used > 0:
        max_dir_count = max(dir_usage.values())
        # Consider only used directions for min_dir_count
        min_dir_count = min(v for v in dir_usage.values() if v > 0) 
        direction_balance = float(100 * num_dirs_used - 50 * (max_dir_count - min_dir_count))
    return direction_balance

def _calculate_spatial_score(puzzle: list[list[str]], locations: dict) -> float:
    """Calculates score based on spatial distribution of words."""
    if not locations or not puzzle or len(puzzle) == 0 or len(puzzle[0]) == 0:
        return 0.0
        
    total_r, total_c = 0.0, 0.0
    total_cells_in_words = 0
    
    for word, ((r0, c0), (rf, cf)) in locations.items():
        word_len = len(word)
        dr = 1 if rf > r0 else (-1 if rf < r0 else 0)
        dc = 1 if cf > c0 else (-1 if cf < c0 else 0)
        r, c = float(r0), float(c0)
        for _ in range(word_len):
            total_r += r
            total_c += c
            total_cells_in_words += 1
            r += dr
            c += dc
            
    avg_r = total_r / total_cells_in_words if total_cells_in_words > 0 else len(puzzle) / 2.0
    avg_c = total_c / total_cells_in_words if total_cells_in_words > 0 else len(puzzle[0]) / 2.0
    
    ideal_r, ideal_c = len(puzzle) / 2.0, len(puzzle[0]) / 2.0
    center_distance = ((avg_r - ideal_r) ** 2 + (avg_c - ideal_c) ** 2) ** 0.5
    
    spatial_score = 300.0 - min(300.0, center_distance * 30.0)
    return spatial_score

def evaluate_puzzle(puzzle: list[list[str]], locations: dict, words_placed: int) -> float:
    """Evaluate the quality of the current puzzle configuration.
    Returns a score where higher is better."""
    
    current_locations = locations if locations is not None else {}

    words_score_val = _calculate_words_score(words_placed, current_locations, WORDS_PER_PUZZLE)
    
    crossings, _filled_cells, density = _calculate_cell_metrics(puzzle, current_locations)
    density_bonus_val = _calculate_density_bonus(density)
    
    direction_balance_val = _calculate_direction_balance_score(current_locations, DIRECTIONS)
    
    spatial_score_val = _calculate_spatial_score(puzzle, current_locations)
    
    return words_score_val + crossings * 30 + direction_balance_val + density_bonus_val + spatial_score_val
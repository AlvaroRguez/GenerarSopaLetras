# evaluation.py

from config import DIRECTIONS

def evaluate_puzzle(puzzle: list[list[str]], locations: dict, words_placed: int) -> float:
    """Evaluate the quality of the current puzzle configuration.
    Returns a score where higher is better."""
    from config import WORDS_PER_PUZZLE
    
    # Prioridad máxima: número de palabras colocadas
    words_score = words_placed * 200  # Aumentado significativamente
    
    # Bonus por alcanzar exactamente el número objetivo de palabras
    target_words = min(WORDS_PER_PUZZLE, len(locations.keys()))
    if words_placed == target_words:
        words_score += 3000  # Bonus muy alto por tener exactamente el número requerido
    elif words_placed >= target_words * 0.9:
        words_score += 1000  # Bonus por estar cerca del objetivo
    
    # Count real word crossings (intersecciones entre palabras)
    crossings = 0
    filled_cells = 0
    cell_usage = {}  # Para contar cuántas palabras usan cada celda
    
    # Mapear qué celdas pertenecen a qué palabras
    for word, ((r0, c0), (rf, cf)) in locations.items():
        dr = 1 if rf > r0 else (-1 if rf < r0 else 0)
        dc = 1 if cf > c0 else (-1 if cf < c0 else 0)
        r, c = r0, c0
        for _ in range(len(word)):
            cell_usage[(r, c)] = cell_usage.get((r, c), 0) + 1
            r += dr
            c += dc
    
    # Contar intersecciones reales y celdas ocupadas
    for (r, c), count in cell_usage.items():
        filled_cells += 1
        if count > 1:
            crossings += count - 1  # Cada uso adicional es una intersección
    
    # Calcular densidad de la sopa (porcentaje de celdas utilizadas)
    density = filled_cells / (len(puzzle) * len(puzzle[0]))
    density_score = 0
    
    # Preferir una densidad óptima (ni muy vacía ni muy llena)
    if 0.4 <= density <= 0.7:  # Rango óptimo
        density_score = 500  # Bonus por densidad óptima
    elif 0.3 <= density < 0.4 or 0.7 < density <= 0.8:
        density_score = 200  # Densidad aceptable
    
    # Calculate direction balance (distribución de direcciones)
    dir_usage = {d: 0 for d in DIRECTIONS}
    for _, ((r0, c0), (rf, cf)) in locations.items():
        if rf == r0:  # Horizontal
            dir_usage[(0, 1 if cf > c0 else -1)] += 1
        elif cf == c0:  # Vertical
            dir_usage[(1 if rf > r0 else -1, 0)] += 1
        else:  # Diagonal
            dir_usage[(1 if rf > r0 else -1, 1 if cf > c0 else -1)] += 1
    
    # Calcular balance de direcciones (mejor si hay variedad)
    if dir_usage:
        max_dir_count = max(dir_usage.values())
        min_dir_count = min(dir_usage.values())
        num_dirs_used = sum(1 for count in dir_usage.values() if count > 0)
        
        # Penalizar desbalance y premiar variedad
        direction_balance = 100 * num_dirs_used - 50 * (max_dir_count - min_dir_count)
    else:
        direction_balance = 0
    
    # Calcular distribución espacial (mejor si las palabras están bien distribuidas)
    spatial_score = 0
    if locations:
        # Calcular centro de masa de las palabras
        total_r, total_c = 0, 0
        total_cells = 0
        
        for word, ((r0, c0), (rf, cf)) in locations.items():
            word_len = len(word)
            # Añadir todas las celdas de la palabra al centro de masa
            dr = 1 if rf > r0 else (-1 if rf < r0 else 0)
            dc = 1 if cf > c0 else (-1 if cf < c0 else 0)
            r, c = r0, c0
            for _ in range(word_len):
                total_r += r
                total_c += c
                total_cells += 1
                r += dr
                c += dc
        
        # Centro de masa
        avg_r = total_r / total_cells if total_cells > 0 else len(puzzle) / 2
        avg_c = total_c / total_cells if total_cells > 0 else len(puzzle[0]) / 2
        
        # Centro ideal (centro del puzzle)
        ideal_r, ideal_c = len(puzzle) / 2, len(puzzle[0]) / 2
        
        # Distancia del centro de masa al centro ideal
        center_distance = ((avg_r - ideal_r) ** 2 + (avg_c - ideal_c) ** 2) ** 0.5
        
        # Mejor puntuación si el centro de masa está cerca del centro del puzzle
        spatial_score = 300 - min(300, center_distance * 30)
    
    # Final score combines multiple factors with pesos ajustados
    return words_score + crossings * 30 + direction_balance + density_score + spatial_score
# backtracking.py

import random
from config import DIRECTIONS, WORDS_PER_PUZZLE
from word_placement import find_candidates, place_word, remove_word, fill_empty_spaces
from evaluation import evaluate_puzzle
from backtracking_utils import try_random_placement, create_fallback_solution
from tqdm import tqdm

def backtracking_word_search(words: list[str], rows: int, columns: int, max_depth: int = 20) -> tuple[list[list[str]], dict]:
    """Generate a word search puzzle using backtracking to optimize global word placement.
    Garantiza que se coloquen exactamente WORDS_PER_PUZZLE palabras (o todas si hay menos)."""
    puzzle = [['' for _ in range(columns)] for _ in range(rows)]
    dir_counts = {d: 0 for d in DIRECTIONS}
    locations = {}
    best_puzzle = None
    best_locations = None
    best_score = -float('inf')
    target_words = min(WORDS_PER_PUZZLE, len(words))
    
    # Asegurarnos de tener suficientes palabras para intentar
    if len(words) < target_words * 2:
        # Duplicar palabras para tener más opciones
        words = words * 2
    
    def backtrack(index: int, depth: int = 0):
        nonlocal best_puzzle, best_locations, best_score
        
        # Si ya encontramos una solución con el número exacto de palabras requeridas
        # y con un buen puntaje, podemos terminar temprano
        if best_locations and len(best_locations) == target_words and best_score > 2000:
            return
        
        # Base case: all words processed or max depth reached
        if index >= len(words) or depth >= max_depth:
            # Evaluate current configuration
            score = evaluate_puzzle(puzzle, locations, len(locations))
            
            # Priorizar soluciones que tengan exactamente el número de palabras requerido
            if len(locations) == target_words:
                score += 5000  # Bonus muy significativo por tener el número exacto de palabras
            elif len(locations) >= target_words * 0.9:  # Al menos 90% de las palabras objetivo
                score += 1000  # Bonus menor pero significativo
            
            if score > best_score:
                best_score = score
                best_puzzle = [row[:] for row in puzzle]  # Deep copy
                best_locations = locations.copy()
                tqdm.write(f"Nueva mejor solución: {len(best_locations)} palabras, puntuación {best_score}")
            return
        
        # Si ya tenemos suficientes palabras, podemos terminar esta rama
        if len(locations) >= target_words:
            # Evaluar y guardar si es mejor que lo que tenemos
            score = evaluate_puzzle(puzzle, locations, len(locations)) + 5000
            if score > best_score:
                best_score = score
                best_puzzle = [row[:] for row in puzzle]  # Deep copy
                best_locations = locations.copy()
                tqdm.write(f"¡Solución completa encontrada! {len(best_locations)} palabras, puntuación {best_score}")
            return
        
        word = words[index].upper()
        candidates = find_candidates(word, puzzle, rows, columns, dir_counts)
        
        # Los candidatos ya vienen ordenados por calidad desde find_candidates
        # Limitar candidatos de forma adaptativa
        max_candidates = 40  # Aumentado para explorar más opciones
        if depth > max_depth * 0.5:  # Si estamos a más de la mitad de profundidad
            max_candidates = 20  # Reducir para explorar más ramas
        
        # Seleccionar subconjunto de candidatos
        if len(candidates) > max_candidates:
            candidates = candidates[:max_candidates]
            # Los candidatos ya están ordenados por calidad (desde find_candidates),
            # procesar en ese orden para priorizar los mejores.
        
        # Try each candidate position with estrategia adaptativa
        for match_count, r0, c0, df, dc, quality_score in candidates:
            # Verificar si esta dirección está sobrerrepresentada
            if dir_counts[(df, dc)] > len(locations) / 4 and random.random() < 0.5:
                continue  # Saltar algunas direcciones sobrerrepresentadas
                
            # Place the word
            loc = place_word(word, puzzle, r0, c0, df, dc)
            locations[word] = loc
            dir_counts[(df, dc)] += 1
            
            # Recurse to next word
            backtrack(index + 1, depth + 1)
            
            # Backtrack: remove the word and try another position
            remove_word(word, puzzle, r0, c0, df, dc)
            # Verificar si la palabra existe en el diccionario antes de eliminarla
            if word in locations:
                del locations[word]
            dir_counts[(df, dc)] -= 1
            
            # Si ya encontramos una solución óptima, podemos terminar temprano
            if best_locations and len(best_locations) == target_words and best_score > 3000:
                return
        
        # If no candidates or we need to explore more options, try random placement
        if not candidates or (depth < max_depth * 0.5 and random.random() < 0.2):  # 20% de probabilidad de intentar aleatorio
            if try_random_placement(word, puzzle, rows, columns, locations, dir_counts, max_tries=500):  # Aumentado significativamente
                backtrack(index + 1, depth + 1)
                
                # Obtener las coordenadas para eliminar la palabra
                if word in locations:  # Verificar primero si la palabra existe en el diccionario
                    ((r0, c0), _) = locations[word]
                    df, dc = 0, 0
                    for direction, count in dir_counts.items():
                        if count > 0:  # Encontrar la dirección que se incrementó
                            df, dc = direction
                            break
                    
                    remove_word(word, puzzle, r0, c0, df, dc)
                    del locations[word]
                    dir_counts[(df, dc)] -= 1
    
    # Ordenar palabras por longitud (más largas primero) para mejorar la colocación
    words = sorted(words, key=lambda w: -len(w))
    
    # Start backtracking from the first word
    backtrack(0)
    
    # Si el backtracking no encontró una solución o no colocó suficientes palabras, implementar solución de fallback
    if best_puzzle is None or len(best_locations) < target_words:
        tqdm.write(f"Usando solución de fallback para colocar {target_words} palabras")
        return create_fallback_solution(words, rows, columns)
    
    # Fill empty spaces in the best puzzle found
    fill_empty_spaces(best_puzzle, rows, columns)
    
    return best_puzzle, best_locations
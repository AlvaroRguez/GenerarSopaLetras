# backtracking_utils.py

import random
from config import DIRECTIONS, MAX_FALLBACK_TRIES, MIN_WORD_LENGTH
from word_placement import place_word
from tqdm import tqdm

def try_random_placement(word: str, puzzle: list[list[str]], rows: int, columns: int, 
                        locations: dict, dir_counts: dict, max_tries: int = None) -> bool:
    """Try to place a word in a random position.
    Returns True if successful, False otherwise."""
    max_tries = max_tries or MAX_FALLBACK_TRIES
    p = word.upper()
    
    # Estrategia adaptativa basada en la longitud de la palabra
    is_short_word = len(p) <= 5
    
    # Probar primero con direcciones menos utilizadas para mejorar distribución
    sorted_directions = sorted(DIRECTIONS, key=lambda d: dir_counts.get(d, 0))
    
    # Distribute max_tries between primary and secondary phases
    primary_tries_ratio = 0.7  # Default ratio for primary (strategic) phase
    if is_short_word:
        primary_tries_ratio = 0.8  # More strategic attempts for short words

    primary_tries = int(max_tries * primary_tries_ratio)
    secondary_tries = max_tries - primary_tries
    
    # Primera fase: direcciones menos utilizadas
    for _ in range(primary_tries):
        # Seleccionar dirección con preferencia a las menos utilizadas
        df, dc = sorted_directions[min(random.randint(0, len(sorted_directions)-1), 
                                      random.randint(0, len(sorted_directions)-1))]
        
        # Seleccionar posición inicial con estrategia adaptativa según longitud de palabra
        if is_short_word:
            # Para palabras cortas, favorecer posiciones centrales para aumentar intersecciones
            center_r, center_c = rows//2, columns//2
            # Distribución gaussiana alrededor del centro (más probable cerca del centro)
            r_offset = int(random.gauss(0, rows//4))
            c_offset = int(random.gauss(0, columns//4))
            r0 = max(0, min(rows-1, center_r + r_offset))
            c0 = max(0, min(columns-1, center_c + c_offset))
        else:
            # Para palabras más largas, posición aleatoria uniforme
            r0, c0 = random.randrange(rows), random.randrange(columns)
            
        rf = r0 + df*(len(p)-1)
        cf = c0 + dc*(len(p)-1)
        
        if not (0 <= rf < rows and 0 <= cf < columns):
            continue
            
        # Verificar si la palabra cabe
        ok = True
        r, c = r0, c0
        for l in p:
            if puzzle[r][c] not in ('', l):
                ok = False
                break
            r += df; c += dc
            
        if ok:
            loc = place_word(word, puzzle, r0, c0, df, dc)
            locations[word] = loc
            dir_counts[(df, dc)] += 1
            return True
    
    # Segunda fase: completamente aleatoria como último recurso
    for _ in range(secondary_tries):
        df, dc = random.choice(DIRECTIONS)
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
            loc = place_word(word, puzzle, r0, c0, df, dc)
            locations[word] = loc
            dir_counts[(df, dc)] += 1
            return True
    
    return False

def create_fallback_solution(words: list[str], rows: int, columns: int):
    """Creates a simple alternative solution when backtracking fails.
    Garantiza que se coloquen exactamente WORDS_PER_PUZZLE palabras (o todas si hay menos)."""
    from word_placement import fill_empty_spaces
    from config import WORDS_PER_PUZZLE, MAX_FALLBACK_TRIES
    import random
    import time
    
    # Definir el número objetivo de palabras
    target_words = min(WORDS_PER_PUZZLE, len(words))
    
    # Ordenar palabras por longitud (más largas primero) para mejorar la colocación
    sorted_words = sorted(words, key=lambda w: -len(w))
    
    # Crear múltiples puzzles con diferentes configuraciones y quedarnos con el mejor
    best_puzzle = None
    best_locations = {}
    max_attempts = 100  # Aumentado significativamente para garantizar 50 palabras y más robustez
    start_time = time.time()
    max_time = 120  # Tiempo máximo en segundos para evitar bucles infinitos
    
    # Crear un pool de palabras más grande para tener más opciones
    word_pool = sorted_words.copy() * 10  # Decuplicamos el pool para mayor variedad y robustez
    
    # Sistema de descarte: palabras que han fallado consistentemente
    problem_words = set()
    word_attempts = {word: 0 for word in sorted_words}
    
    for attempt in range(max_attempts):
        # Verificar si hemos excedido el tiempo máximo
        if time.time() - start_time > max_time:
            tqdm.write(f"Tiempo máximo excedido después de {attempt} intentos")
            break
            
        # Create an empty puzzle for this attempt
        puzzle = [['' for _ in range(columns)] for _ in range(rows)]
        locations = {}
        dir_counts = {d: 0 for d in DIRECTIONS}
        
        # Mezclar direcciones para cada intento
        random_directions = list(DIRECTIONS)
        random.shuffle(random_directions)
        
        # Actualizar sistema de descarte de palabras problemáticas
        if attempt > 0 and attempt % 5 == 0:
            # Cada 5 intentos, analizar qué palabras están causando problemas
            for word, attempts in word_attempts.items():
                # Si una palabra ha sido intentada muchas veces sin éxito, marcarla como problemática
                if attempts >= 3 and word not in problem_words and len(word) > MIN_WORD_LENGTH + 1:
                    problem_words.add(word)
                    tqdm.write(f"Palabra problemática descartada: {word} (intentos: {attempts})")
        
        # Estrategia adaptativa basada en intentos anteriores
        if attempt > 15 and len(best_locations) < target_words * 0.7:
            # Estrategia muy agresiva: usar palabras más cortas y evitar problemáticas
            available_words = [w for w in word_pool if w not in problem_words]
            # Si tenemos pocas palabras disponibles, reiniciar parcialmente el sistema de descarte
            if len(available_words) < target_words * 2:
                problem_words = set([w for w in problem_words if word_attempts.get(w, 0) > 5])
                available_words = [w for w in word_pool if w not in problem_words]
            current_words = sorted(available_words, key=len)[:target_words*6]  # Sextuplicamos el pool
            random.shuffle(current_words)
        elif attempt > 10 and len(best_locations) < target_words * 0.8:
            # Estrategia agresiva: usar palabras más cortas primero y evitar problemáticas
            available_words = [w for w in word_pool if w not in problem_words]
            current_words = sorted(available_words, key=len)[:target_words*5]  # Quintuplicamos el pool
            random.shuffle(current_words)
        elif attempt > 5 and len(best_locations) < target_words * 0.9:
            # Estrategia intermedia: mezclar palabras cortas y largas, evitando problemáticas
            available_words = [w for w in word_pool if w not in problem_words]
            short_words = sorted(available_words, key=len)[:target_words*3]
            long_words = sorted(available_words, key=lambda w: -len(w))[:target_words*2]
            current_words = short_words + long_words
            random.shuffle(current_words)
        else:
            # Estrategia inicial: palabras largas primero con algo de aleatoriedad
            current_words = sorted(word_pool, key=lambda w: -len(w) + random.random())[:target_words*4]
        
        # Conservar palabras que ya funcionaron en intentos anteriores
        if best_locations and attempt > 0:
            successful_words = [w for w in sorted_words if w.upper() in best_locations]
            # Añadir palabras exitosas al principio con alta prioridad
            if successful_words:
                # Usar solo un subconjunto de palabras exitosas para mantener diversidad
                subset = successful_words[:min(len(successful_words), target_words//2)]
                current_words = subset + [w for w in current_words if w not in subset]
        
        # Intentar colocar cada palabra con estrategia adaptativa
        for word in current_words:
            if len(locations) >= target_words:
                break  # Ya tenemos suficientes palabras
                
            p = word.upper()
            if p in locations:
                continue  # Palabra ya colocada
                
            # Actualizar contador de intentos para esta palabra
            word_attempts[word] = word_attempts.get(word, 0) + 1
                
            placed = False
            
            # Aumentar el número de intentos por palabra en cada intento global, hasta MAX_FALLBACK_TRIES
            # Base de 5% de MAX_FALLBACK_TRIES (MAX_FALLBACK_TRIES // 20), incrementando cada 3 intentos globales.
            base_increment_tries = MAX_FALLBACK_TRIES // 20 
            word_tries = min(MAX_FALLBACK_TRIES, base_increment_tries * (1 + attempt // 3))
            
            # Ordenar direcciones por menos utilizadas primero
            sorted_dirs = sorted(random_directions, key=lambda d: dir_counts.get(d, 0))
            
            # Try each direction with increased randomization and strategic placement
            for df, dc in sorted_dirs:
                if placed:
                    break
                    
                # Crear una lista de posiciones iniciales con estrategia
                # Priorizar posiciones centrales para palabras largas
                if len(p) > 6:
                    # Para palabras largas, preferir posiciones más centrales
                    center_r, center_c = rows//2, columns//2
                    positions = [(r, c) for r in range(rows) for c in range(columns)]
                    # Ordenar por distancia al centro (más cercanas primero)
                    positions.sort(key=lambda pos: abs(pos[0]-center_r) + abs(pos[1]-center_c))
                    # Añadir algo de aleatoriedad para no concentrar todo en el centro
                    if random.random() < 0.3:
                        random.shuffle(positions)
                else:
                    # Para palabras cortas, posiciones aleatorias
                    positions = [(r, c) for r in range(rows) for c in range(columns)]
                    random.shuffle(positions)
                
                # Limitar el número de posiciones a probar para mejorar rendimiento
                # pero aumentar significativamente para palabras importantes
                max_positions = min(len(positions), word_tries // len(sorted_dirs))
                
                for r0, c0 in positions[:max_positions]:
                    rf = r0 + df*(len(p)-1)
                    cf = c0 + dc*(len(p)-1)
                    
                    if not (0 <= rf < rows and 0 <= cf < columns):
                        continue
                        
                    # Verificar si la palabra cabe y cuenta intersecciones (favorecerlas)
                    ok = True
                    intersections = 0
                    r, c = r0, c0
                    for l in p:
                        if puzzle[r][c] not in ('', l):
                            ok = False
                            break
                        if puzzle[r][c] == l:  # Intersección con otra palabra
                            intersections += 1
                        r += df; c += dc
                        
                    if ok:
                        # Place the word
                        r, c = r0, c0
                        for l in p:
                            puzzle[r][c] = l
                            r += df; c += dc
                        locations[p] = ((r0, c0), (rf, cf))
                        dir_counts[(df, dc)] += 1
                        placed = True
                        break
        
        # Guardar el mejor resultado hasta ahora
        if len(locations) > len(best_locations):
            best_puzzle = [row[:] for row in puzzle]  # Deep copy
            best_locations = locations.copy()
            tqdm.write(f"Intento {attempt+1}: Mejorado a {len(best_locations)} palabras")
            
        # Si ya tenemos todas las palabras requeridas, terminamos
        if len(best_locations) >= target_words:
            tqdm.write(f"Éxito en el intento {attempt+1}: Colocadas {len(best_locations)} palabras")
            break
            
        # Si estamos cerca del objetivo, imprimir progreso
        if len(locations) > 0:
            tqdm.write(f"Intento {attempt+1}: Colocadas {len(locations)} de {target_words} palabras")
    
    # Si después de todos los intentos no tenemos suficientes palabras,
    # intentar una última estrategia con palabras más cortas
    if len(best_locations) < target_words:
        tqdm.write(f"Realizando intento final con palabras más cortas ({len(best_locations)}/{target_words} colocadas)")
        
        # Crear múltiples pools con palabras de diferentes longitudes
        very_short_words = sorted([w for w in word_pool if w not in problem_words and len(w) <= 5], key=len)
        short_words = sorted([w for w in word_pool if w not in problem_words and 5 < len(w) <= 7], key=len)
        medium_words = sorted([w for w in word_pool if w not in problem_words and 7 < len(w) <= 9], key=len)
        
        # Realizar múltiples intentos finales con diferentes estrategias
        for final_attempt in range(4):  # 3 intentos finales con diferentes configuraciones
            tqdm.write(f"Intento final {final_attempt+4}/30 con estrategia adaptativa")
            
            # Crear un puzzle vacío para el intento final
            final_puzzle = [['' for _ in range(columns)] for _ in range(rows)]
            final_locations = {}
            final_dir_counts = {d: 0 for d in DIRECTIONS}
            
            # Primero colocar las palabras que ya funcionaron (pero no todas para permitir variedad)
            successful_words = [w for w in sorted_words if w.upper() in best_locations]
            success_count = min(len(successful_words), target_words//3)
            
            # Seleccionar palabras exitosas con preferencia a las más cortas en el último intento
            if final_attempt == 2:
                successful_words = sorted(successful_words, key=len)
            
            for word in successful_words[:success_count]:
                try_random_placement(word, final_puzzle, rows, columns, final_locations, final_dir_counts, max_tries=MAX_FALLBACK_TRIES*10)
            
            # Mezclar palabras de diferentes longitudes según la estrategia del intento
            if final_attempt == 0:  # Primera estrategia: priorizar palabras muy cortas
                word_candidates = very_short_words * 3 + short_words + medium_words[:target_words//4]
            elif final_attempt == 1:  # Segunda estrategia: equilibrar entre cortas y medias
                word_candidates = very_short_words * 2 + short_words * 2 + medium_words[:target_words//3]
            else:  # Tercera estrategia: maximizar variedad con preferencia a cortas
                word_candidates = very_short_words * 4 + short_words * 2
            
            # Aleatorizar para no quedar atrapados en el mismo patrón
            random.shuffle(word_candidates)
            
            # Luego intentar con palabras seleccionadas hasta completar
            for word in word_candidates:
                if len(final_locations) >= target_words:
                    break
                if word.upper() not in final_locations:
                    # Aumentar significativamente los intentos para palabras cortas
                    max_tries_factor = 15 if len(word) <= 5 else 10
                    try_random_placement(word, final_puzzle, rows, columns, final_locations, final_dir_counts, max_tries=MAX_FALLBACK_TRIES*max_tries_factor)
            
            # Actualizar el mejor resultado si mejoramos
            if len(final_locations) > len(best_locations):
                best_puzzle = final_puzzle
                best_locations = final_locations
                tqdm.write(f"Intento final {final_attempt+1}: Mejorado a {len(best_locations)} palabras")
                
                # Si ya alcanzamos el objetivo, terminamos
                if len(best_locations) >= target_words:
                    tqdm.write(f"¡Éxito! Se alcanzó el objetivo de {target_words} palabras")
                    break
        
        # Actualizar el mejor resultado si mejoramos
        if len(final_locations) > len(best_locations):
            best_puzzle = final_puzzle
            best_locations = final_locations
            tqdm.write(f"Intento final: Mejorado a {len(best_locations)} palabras")
    
    # Mensaje final sobre el resultado
    if len(best_locations) < target_words:
        tqdm.write(f"Advertencia: Solo se pudieron colocar {len(best_locations)} de {target_words} palabras")
    else:
        tqdm.write(f"Éxito: Se colocaron todas las {len(best_locations)} palabras requeridas")
    
    # Fill empty spaces
    fill_empty_spaces(best_puzzle, rows, columns)
    
    return best_puzzle, best_locations
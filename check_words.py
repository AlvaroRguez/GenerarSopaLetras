# check_words.py

import os
import random
import pickle

from config import USE_LOOKFOR, WORDS_PER_PUZZLE, PUZZLE_ROWS, PUZZLE_COLUMNS
from generator import generate_word_search, build_filtered_dict
from data_loader import get_raw_words, load_blacklist

print("🔍 Generando sopas de letras para verificar…\n")

# 1) Cargar y filtrar palabras
raw = get_raw_words()
print(f"Cargadas {len(raw)} palabras en bruto.")
blacklist = load_blacklist()
filtered = build_filtered_dict(raw, blacklist)
print(f"Filtradas a {len(filtered)} palabras.\n")

# 2) Probar N puzzles
num_puzzles = 5
print(f"⚙️  Generando {num_puzzles} sopas de letras de prueba:")
print(f"   • Palabras esperadas por puzzle: {WORDS_PER_PUZZLE}")
print("   • Palabras realmente colocadas en cada puzzle:")

for i in range(1, num_puzzles + 1):
    selection = random.sample(filtered, WORDS_PER_PUZZLE)
    result = generate_word_search(selection, PUZZLE_ROWS, PUZZLE_COLUMNS, USE_LOOKFOR)

    # Compatibilidad: si devuelve 3 elementos, desempacamos tres; si son 2, adaptamos
    if len(result) == 3:
        puzzle, placed_words, locations = result
    else:
        puzzle, locations = result
        placed_words = list(locations.keys())

    tqdm.write(f"   Puzzle {i}: {len(placed_words)} palabras de {WORDS_PER_PUZZLE}")

# 3) (Opcional) Si no hay puzzles en memoria y deseas cargar un .pkl
if num_puzzles == 0:
    tqdm.write("\nNo se generaron puzzles en memoria. Buscando .docx.pkl…")
    for fn in os.listdir('.'):
        if fn.endswith('.docx.pkl'):
            tqdm.write(f"🔄 Analizando archivo: {fn}")
            with open(fn, 'rb') as f:
                try:
                    puzzles = pickle.load(f)
                except Exception as e:
                    tqdm.write(f"❌ Error al cargar {fn}: {e}")
                    break

            tqdm.write(f"   • Palabras esperadas por puzzle: {WORDS_PER_PUZZLE}")
            for idx, (puz, words, locs) in enumerate(puzzles, 1):
                tqdm.write(f"   Puzzle {idx}: {len(locs)} palabras de {len(words)}")
            break

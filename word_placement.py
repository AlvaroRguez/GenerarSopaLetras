# word_placement.py

import random
from config import DIRECTIONS, ALPHABET


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
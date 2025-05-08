# drawing.py

import matplotlib.pyplot as plt
from config import PDF_PUZZLE_FONT, PDF_SOLUTION_FONT
from typing import List, Dict, Tuple

def draw_puzzle(ax, puzzle: list[list[str]], fontsize_input = PDF_SOLUTION_FONT) -> None:
    """Draws the word search grid."""    
    rows, cols = len(puzzle), len(puzzle[0])
    ax.axis('off')
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_aspect('equal')
    # outer border
    ax.plot([0, cols], [0, 0], color='black')
    ax.plot([cols, cols], [0, rows], color='black')
    ax.plot([cols, 0], [rows, rows], color='black')
    ax.plot([0, 0], [rows, 0], color='black')
    # letters
    for i in range(rows):
        for j in range(cols):
            ax.text(j + 0.5, rows - i - 0.5,
                    puzzle[i][j],
                    va='center', ha='center',
                    fontsize=fontsize_input)

def draw_solution(ax, puzzle: list[list[str]],
                  locations: dict[str,tuple[tuple[int,int],tuple[int,int]]]
) -> None:
    """Draws the solution with red lines."""
    rows, cols = len(puzzle), len(puzzle[0])
    draw_puzzle(ax, puzzle)  # reuse the grid
    for word, ((r0,c0),(rf,cf)) in locations.items():
        x0, y0 = c0 + 0.5, rows - r0 - 0.5
        x1, y1 = cf + 0.5, rows - rf - 0.5
        ax.plot([x0, x1], [y0, y1], color='red', linewidth=2)

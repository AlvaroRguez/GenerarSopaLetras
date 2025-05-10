# export_pdf.py

import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from tqdm import tqdm
from drawing import draw_puzzle, draw_solution
from config import *

def create_pdf(all_puzzles, name: str = f"{TOTAL_PUZZLES}_word_search_puzzles.pdf"):
    with PdfPages(name) as pp:
        for idx, (puzzle, words, _) in enumerate(
            tqdm(all_puzzles, desc="PDF: puzzles", unit="puzzle", ncols=TQDM_COLS),
            start=1
        ):
            fig = plt.figure(figsize=PDF_PAGE_SIZE)
            # title
            fig.text(
                0.5, 1 - PDF_PUZZLE_AREA['bottom'] + 0.02,
                f"Sopa de letra Nº: {idx}",
                ha='center', va='top',
                fontsize=PDF_TITLE_FONT['size'],
                weight=PDF_TITLE_FONT['weight']
            )
            # grid
            ax = fig.add_axes([
                PDF_PUZZLE_AREA['left'],
                PDF_PUZZLE_AREA['bottom'],
                PDF_PUZZLE_AREA['width'],
                PDF_PUZZLE_AREA['height']
            ])
            draw_puzzle(ax, puzzle, PDF_PUZZLE_FONT)
            # word list
            cols, per_col = SEARCH_WORDS_COLS, math.ceil(len(words)/SEARCH_WORDS_COLS)
            gap = PDF_PUZZLE_AREA['width'] / cols
            x_positions = [PDF_PUZZLE_AREA['left'] + gap/2 + i*gap for i in range(cols)]
            y_start, y_step = PDF_PUZZLE_AREA['bottom'] - 0.02, PDF_PUZZLE_AREA['height']/per_col
            for i, w in enumerate(words):
                col = i % cols
                row = i // cols
                fig.text(
                    x_positions[col],
                    y_start - row*y_step,
                    w.upper(),
                    va='top', ha='center',
                    fontsize=PDF_WORDLIST_FONT
                )
            pp.savefig(fig)
            plt.close(fig)

        # solution pages
        per_page = SOLUTION_PER_PAGE
        pages = math.ceil(len(all_puzzles)/per_page)
        for page_idx, start in enumerate(
            tqdm(range(0, len(all_puzzles), per_page),
                 desc="PDF: solutions", unit="pages",
                 total=pages, ncols=TQDM_COLS),
            start=1
        ):
            fig = plt.figure(figsize=PDF_PAGE_SIZE)
            for sub, loc in enumerate(range(start, min(start+per_page, len(all_puzzles)))):
                puzzle, _, locs = all_puzzles[loc]
                col = sub % 2
                row = sub // 2
                left = 0.05 + col*0.475
                bottom = 0.05 + (4-row)*0.18
                ax = fig.add_axes([left, bottom, 0.45, 0.18])
                draw_solution(ax, puzzle, locs)
                ax.text(-0.1, 0.5, f"Puzzle {loc+1}",
                        va='center', ha='right', rotation=90,
                        fontsize=PDF_WORDLIST_FONT,
                        transform=ax.transAxes)
            pp.savefig(fig)
            plt.close(fig)

    tqdm.write(f"PDF generated: {name}")

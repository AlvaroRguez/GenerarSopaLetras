import random
import sys
import io
import math
import json
import time
from numpy.char import center
from tqdm import tqdm

try:
    from wordfreq import top_n_list
except ImportError:
    print("Missing 'wordfreq' library. Install it with: pip install wordfreq", file=sys.stderr)
    sys.exit(1)

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT

import enchant  # make sure you have pyenchant installed and the es_ES dict configured

WORDS_PER_PUZZLE = 50
PUZZLE_ROWS, PUZZLE_COLUMNS = 14, 17
TOTAL_PUZZLES = 365
SEARCH_WORDS_COLS = 5

def load_blacklist_from_json(filename):
    blacklist = set()
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if isinstance(data, (list, set)):
                blacklist.update(word.lower() for word in data)
            else:
                print(f"Warning: '{filename}' does not contain a valid list or set.")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except json.JSONDecodeError:
        print(f"Error: File '{filename}' is not a valid JSON.")
    return blacklist

blacklist = load_blacklist_from_json('blacklist.json')

def is_word_allowed(word, blacklist):
    return word.lower() not in blacklist

def generate_word_search(words, rows=PUZZLE_ROWS, columns=PUZZLE_COLUMNS):
    # 0) Reorder words from longest to shortest to maximize crossings
    words = sorted(words, key=lambda w: -len(w))
    puzzle = [['' for _ in range(columns)] for _ in range(rows)]
    directions = [(0,1),(1,0),(0,-1),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
    # Initialize a direction counter
    dir_counts = {d: 0 for d in directions}
    locations = {}

    for word in words:
        p = word.upper()
        candidates = []
        # 1) Explore all possible positions
        for df, dc in directions:
            for r0 in range(rows):
                for c0 in range(columns):
                    rf = r0 + df*(len(p)-1)
                    cf = c0 + dc*(len(p)-1)
                    if not (0 <= rf < rows and 0 <= cf < columns):
                        continue
                    match_count = 0
                    ok = True
                    r, c = r0, c0
                    for l in p:
                        if puzzle[r][c] == l:
                            match_count += 1
                        elif puzzle[r][c] not in ('',):
                            ok = False
                            break
                        r += df; c += dc
                    if ok:
                        candidates.append((match_count, r0, c0, df, dc))
        # 2) If there are candidates, filter to favor less used directions
        if candidates:
            # Sort candidates by match_count (descending)
            candidates.sort(key=lambda x: x[0], reverse=True)
            # Now, among the best, choose the direction with least usage
            # Collect candidates with maximum match_count
            max_match = candidates[0][0]
            top = [c for c in candidates if c[0] == max_match]
            # Sort top by dir_counts[(df,dc)] ascending
            top.sort(key=lambda x: dir_counts[(x[3], x[4])])
            # Choose the first one
            _, r0, c0, df, dc = top[0]
            rf = r0 + df*(len(p)-1)
            cf = c0 + dc*(len(p)-1)
        else:
            # Brief fallback: random placement without mandatory crossing
            placed = False
            for _ in range(200):
                df, dc = random.choice(directions)
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
                    placed = True
                    break
            if not placed:
                continue
        # 3) Place the word and update direction counter
        r, c = r0, c0
        for l in p:
            puzzle[r][c] = l
            r += df; c += dc
        locations[p] = ((r0, c0), (rf, cf))
        dir_counts[(df, dc)] += 1   # count the usage of this direction

    # 4) Fill empty spaces
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for i in range(rows):
        for j in range(columns):
            if puzzle[i][j] == '':
                puzzle[i][j] = random.choice(alphabet)

    return puzzle, locations

def draw_puzzle(ax, puzzle):
    rows, columns = len(puzzle), len(puzzle[0])
    ax.axis('off')
    ax.set_xlim(0, columns)
    ax.set_ylim(0, rows)
    ax.set_aspect('equal')
    # Outer border
    ax.plot([0, columns], [0, 0], color='black')
    ax.plot([columns, columns], [0, rows], color='black')
    ax.plot([columns, 0], [rows, rows], color='black')
    ax.plot([0, 0], [rows, 0], color='black')
    # Letters
    for i in range(rows):
        for j in range(columns):
            ax.text(j + 0.5, rows - i - 0.5, puzzle[i][j], va='center', ha='center', fontsize=12)

def draw_solution(ax, puzzle, locations):
    rows, columns = len(puzzle), len(puzzle[0])
    ax.axis('off')
    ax.set_xlim(0, columns)
    ax.set_ylim(0, rows)
    ax.set_aspect('equal')
    ax.plot([0, columns], [0, 0], color='black')
    ax.plot([columns, columns], [0, rows], color='black')
    ax.plot([columns, 0], [rows, rows], color='black')
    ax.plot([0, 0], [rows, 0], color='black')
    for i in range(rows):
        for j in range(columns):
            ax.text(j + 0.5, rows - i - 0.5, puzzle[i][j], va='center', ha='center', fontsize=8)
    for word, ((r0, c0), (rf, cf)) in locations.items():
        x0, y0 = c0 + 0.5, rows - r0 - 0.5
        x1, y1 = cf + 0.5, rows - rf - 0.5
        ax.plot([x0, x1], [y0, y1], color='red', linewidth=2)

def create_pdf(all_puzzles, name=f"{TOTAL_PUZZLES}_word_search_puzzles.pdf"):
    with PdfPages(name) as pp:
        # — Puzzle pages —
        for idx, (puzzle, words, _) in enumerate(
            tqdm(all_puzzles,
                 desc="PDF: puzzles",
                 unit="puzzle",
                 ncols=80),
            start=1
        ):
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.text(0.5, 0.97,
                     f"Puzzle {idx} - {len(words)} words",
                     ha='center', va='top', fontsize=14, weight='bold')
            ax = fig.add_axes([0.1, 0.30, 0.8, 0.55])
            draw_puzzle(ax, puzzle)

            # horizontal zone reserved for words:
            left, width = 0.1, 0.8

            cols = SEARCH_WORDS_COLS
            rows = math.ceil(len(words) / cols)

            # space between columns
            gap = width / cols

            # create text positions in X centered within [left,left+width]
            # shift half gap to center each column in its "cell"
            x_positions = [left + gap/2 + i * gap for i in range(cols)]

            # You can adjust y_start depending on how much margin you leave below the puzzle
            y_start = 0.28
            y_step  = 0.55 / rows

            for i, w in enumerate(words):
                col = i % cols
                row = i // cols
                fig.text(
                    x_positions[col],
                    y_start - row * y_step,
                    w.upper(),
                    va='top', ha='center',   # center the text in each column
                    fontsize=10
                )

            pp.savefig(fig)
            plt.close(fig)

        # — Solution pages (10 per page) —
        per_page = 10
        n = len(all_puzzles)
        num_pages = math.ceil(n / per_page)
        for page_idx, start in enumerate(
            tqdm(range(0, n, per_page),
                 desc="PDF: solutions",
                 unit="pages",
                 total=num_pages,
                 ncols=80),
            start=1
        ):
            fig = plt.figure(figsize=(8.27, 11.69))
            for loc in range(start, min(start + per_page, n)):
                puzzle, _, locations = all_puzzles[loc]
                sub = loc - start
                col = sub % 2
                row = sub // 2
                left = 0.05 + col * 0.475
                bottom = 0.05 + (4 - row) * 0.18
                ax = fig.add_axes([left, bottom, 0.45, 0.18])
                draw_solution(ax, puzzle, locations)
                ax.text(-0.1, 0.5,
                        f"Puzzle {loc+1}",
                        va='center', ha='right',
                        rotation=90,
                        fontsize=10,
                        transform=ax.transAxes)
            pp.savefig(fig)
            plt.close(fig)

    print(f"PDF generated: {name}")

def create_docx(all_puzzles, name=f"{TOTAL_PUZZLES}_word_search_puzzles.docx"):
    doc = Document()
    # Cover
    doc.add_heading('Word Search Puzzles', level=1)
    doc.add_page_break()

    # — Puzzles with list —
    for idx, (puzzle, words, _) in enumerate(
        tqdm(all_puzzles,
             desc="DOCX: puzzles",
             unit="puzzle",
             ncols=80),
        start=1
    ):
        doc.add_heading(f'Puzzle {idx} - {len(words)} words', level=2)
        # Generate puzzle image
        fig = plt.figure(figsize=(6, 8))
        ax = fig.add_axes([0,0,1,1])
        draw_puzzle(ax, puzzle)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)

        p = doc.add_paragraph()
        r = p.add_run()
        r.add_picture(buf, width=Inches(6))
        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        # List in columns with calculated rows
        cols = SEARCH_WORDS_COLS
        rows = math.ceil(len(words) / cols)
        table = doc.add_table(rows=rows, cols=cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        for i, w in enumerate(words):
            r_cell = i // cols
            c_cell = i % cols
            cell = table.rows[r_cell].cells[c_cell]
            cell.text = w.upper()
            para = cell.paragraphs[0]
            para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    # — Solutions in mini-grids —
    doc.add_page_break()
    doc.add_heading('Solutions', level=1)

    per_page = 10
    n = len(all_puzzles)
    num_pages = math.ceil(n / per_page)
    for page_idx, start in enumerate(
        tqdm(range(0, n, per_page),
             desc="DOCX: solutions",
             unit="pages",
             total=num_pages,
             ncols=80),
        start=1
    ):
        if page_idx > 1:
            doc.add_page_break()
        group = all_puzzles[start:start+per_page]
        table = doc.add_table(rows=5, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        for i, (puzzle, _, locations) in enumerate(group):
            # Render mini-solution
            fig = plt.figure(figsize=(3, 2.5))
            ax = fig.add_axes([0,0,1,1])
            draw_solution(ax, puzzle, locations)
            ax.text(-0.1, 0.5,
                    f"Puzzle {start+i+1}",
                    va='center', ha='right',
                    rotation=90, fontsize=8,
                    transform=ax.transAxes)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)

            cell = table.rows[i//2].cells[i%2]
            p = cell.paragraphs[0]
            run = p.add_run()
            run.add_picture(buf, width=Inches(2))
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    doc.save(name)
    print(f"Word document generated: {name}")

def main():
    # 1) Frequencies and spell checking filtering
    word_list = top_n_list('es', 100000)
    print(f"Retrieved {len(word_list)} frequent words.")
    d = enchant.Dict("es_ES")
    filtered_dict = [
        w for w in word_list
        if 4 <= len(w) <= 10 and w.isalpha() and d.check(w) and is_word_allowed(w, blacklist)
    ]
    print(f"Filtered dictionary: {len(filtered_dict)} valid words.\n")

    # Word search generation with progress bar
    total_puzzles = TOTAL_PUZZLES
    all_puzzles = []
    used_global = set()
    start_time = time.perf_counter()
    pbar = tqdm(range(total_puzzles), desc="Generating puzzles", unit="puzzle", ncols=80)
    for idx in pbar:
        available = [w for w in filtered_dict if w.upper() not in used_global]
        if len(available) < WORDS_PER_PUZZLE:
            used_global.clear()
            available = filtered_dict.copy()
        selection = random.sample(available, min(WORDS_PER_PUZZLE, len(available)))
        used_global.update(w.upper() for w in selection)
        puzzle, locations = generate_word_search(selection)
        all_puzzles.append((puzzle, [w.upper() for w in selection], locations))
        elapsed = time.perf_counter() - start_time
        pbar.set_postfix({"elapsed": f"{elapsed:.1f}s"})
    pbar.close()

    print("\nGeneration completed.\nCreating PDF and DOCX...")
    create_docx(all_puzzles)
    create_pdf(all_puzzles)
    print("Process finished!")

if __name__ == '__main__':
    main()

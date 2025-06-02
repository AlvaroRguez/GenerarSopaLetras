# export_docx.py

import io
import math
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
# from tqdm import tqdm # Removed tqdm
# from docx2pdf import convert # Removed docx2pdf

from config import * # Assuming this imports necessary constants like TITLE_DOCX etc.
from drawing import draw_puzzle, draw_solution

def create_docx(all_puzzles): # Removed name parameter
    doc = Document()
    # cover
    para = doc.add_heading(TITLE_DOCX, level=1)
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()

    # puzzles
    # Assuming all_puzzles is a list of tuples: (puzzle_grid, placed_words, locations)
    # Ensure PUZZLE_COLUMNS, PUZZLE_ROWS, PDF_PUZZLE_FONT, DOCX_IMAGE_WIDTH, DOCX_PARA_ALIGN etc. are available from config
    for idx, (puzzle, words, _) in enumerate(all_puzzles, start=1):
        # tqdm removed
        para = doc.add_heading(f'{TITLE_DOCX} Nº: {idx} [{len(words)}]', level=DOCX_TITLE_LEVEL)
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # image
        fig = plt.figure(figsize=(PUZZLE_COLUMNS/2, PUZZLE_ROWS/2))
        ax = fig.add_axes([0,0,1,1])
        draw_puzzle(ax, puzzle, PDF_PUZZLE_FONT)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)

        p = doc.add_paragraph()
        r = p.add_run()
        r.add_picture(buf, width=Inches(DOCX_IMAGE_WIDTH))
        p.alignment = DOCX_PARA_ALIGN

        # word table
        cols = SEARCH_WORDS_COLS
        rows = math.ceil(len(words)/cols)
        table = doc.add_table(rows=rows, cols=cols)
        table.alignment = DOCX_TABLE_ALIGN
        table.autofit = False
        sorted_words = sorted(words)
        for i, w in enumerate(sorted_words):
            cell = table.rows[i//cols].cells[i%cols]
            cell.text = w.upper()
            cell.paragraphs[0].alignment = DOCX_PARA_ALIGN

    # solutions
    doc.add_page_break()
    doc.add_heading('Solutions', level=1)
    doc.add_page_break()
    per_page, cols = SOLUTION_PER_PAGE, SOLUTION_COLS
    rows = math.ceil(per_page/cols)
    # pages = math.ceil(len(all_puzzles)/per_page) # Not needed without tqdm
    for page_idx, start in enumerate(range(0, len(all_puzzles), per_page), start=1):
        # tqdm removed
        if page_idx>1:
            doc.add_page_break()
        group = all_puzzles[start:start+per_page]
        table = doc.add_table(rows=rows, cols=cols)
        table.alignment = DOCX_TABLE_ALIGN
        table.autofit = False

        for i,(puz,_,locs) in enumerate(group):
            fig = plt.figure(figsize=(3,2.5))
            ax = fig.add_axes([0,0,1,1])
            draw_solution(ax, puz, locs)
            ax.text(-0.1,0.5,f"Puzzle {start+i+1}",
                    va='center',ha='right',rotation=90,
                    fontsize=PDF_WORDLIST_FONT,
                    transform=ax.transAxes)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)

            cell = table.rows[i//cols].cells[i%cols]
            run = cell.paragraphs[0].add_run()
            run.add_picture(buf, width=Inches(DOCX_SOL_IMG_WIDTH))
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY_HI
            para = cell.paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # doc.save(name) # Removed saving to file
    # tqdm.write(f"Word document generated: {name}") # Removed tqdm

    # pdf_name = name.replace(".docx", ".pdf") # Removed PDF conversion
    # try:
    #     tqdm.write(f"Converting {name} to {pdf_name}...")
    #     convert(name, pdf_name)
    #     tqdm.write(f"PDF document generated: {pdf_name}")
    # except Exception as e:
    #     tqdm.write(f"Error converting DOCX to PDF: {e}")
    #     tqdm.write("Please ensure you have Microsoft Word installed and accessible, or LibreOffice for non-Windows systems, for docx2pdf to function correctly.")

    docx_io = io.BytesIO()
    doc.save(docx_io)
    docx_io.seek(0)
    return docx_io

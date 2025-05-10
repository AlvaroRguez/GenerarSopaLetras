# config.py

from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT

# ——— GENERAL CONFIGURATION ———
VERBOSE           = True

TITLE_DOCX         = "Sopa de Letras"
USE_BACKTRACKING   = True
USE_LOOKFOR        = True
WORD_SOURCE        = "file" #on "wordfreq"
WORD_SOURCE_FILE   = "palabras_todas.txt"
MAX_RAW_WORDS      = 1000000

MIN_WORD_LENGTH    = 4
MAX_WORD_LENGTH    = 10
POS_ALLOWED        = {"NOUN", "VERB", "ADV"}
BLACKLIST_FILE     = "blacklist.json"

# ——— Proporciones para lookfor_sequential_word_search ———
LONG_RATIO    = 0.30   # 30% de WORDS_PER_PUZZLE serán “largas”
MED_RATIO     = 0.40   # 40% “medianas”
SHORT_RATIO   = 0.30   # 30% “cortas”

WORDS_PER_PUZZLE   = 50  # Mantenemos 50 palabras como objetivo
PUZZLE_ROWS        = 14  # Mantenemos las dimensiones actuales
PUZZLE_COLUMNS     = 17  # Mantenemos las dimensiones actuales
MAX_FALLBACK_TRIES = 20000  # Aumentado significativamente para garantizar la colocación de 50 palabras
ALPHABET           = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
DIRECTIONS         = [(0,1),(1,0),(0,-1),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]

TOTAL_PUZZLES      = 365

# PDF settings
PDF_PAGE_SIZE      = (8.27, 11.69)
PDF_PUZZLE_AREA    = dict(left=0.1, bottom=0.30, width=0.8, height=0.55)
SEARCH_WORDS_COLS  = 5
PDF_TITLE_FONT     = dict(size=14, weight='bold')
PDF_PUZZLE_FONT    = 14
PDF_SOLUTION_FONT  = 12
PDF_WORDLIST_FONT  = 10

# DOCX settings
SOLUTION_PER_PAGE  = 15
SOLUTION_COLS      = 3
DOCX_IMAGE_WIDTH   = 6    # inches
DOCX_SOL_IMG_WIDTH = 1.8  # inches
DOCX_TITLE_LEVEL   = 2
DOCX_PARA_ALIGN    = WD_PARAGRAPH_ALIGNMENT.CENTER
DOCX_TABLE_ALIGN   = WD_TABLE_ALIGNMENT.CENTER

TQDM_COLS         = 80
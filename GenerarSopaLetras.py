import random
import sys
import io
import math
import json

try:
    from wordfreq import top_n_list
except ImportError:
    print("Falta la librería ‘wordfreq’. Instálala con: pip install wordfreq", file=sys.stderr)
    sys.exit(1)

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT

def cargar_blacklist_desde_json(nombre_archivo):
    blacklist = set()
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            data = json.load(archivo)
            if isinstance(data, list):
                blacklist.update(palabra.lower() for palabra in data)
            elif isinstance(data, set):
                blacklist.update(palabra.lower() for palabra in data)
            else:
                print(f"Advertencia: El archivo '{nombre_archivo}' no contiene una lista o conjunto.")
    except FileNotFoundError:
        print(f"Error: El archivo '{nombre_archivo}' no se encontró.")
    except json.JSONDecodeError:
        print(f"Error: El archivo '{nombre_archivo}' no es un JSON válido.")
    return blacklist

blacklist = cargar_blacklist_desde_json('blacklist.json')

def es_palabra_permitida(palabra, blacklist):
    return palabra.lower() not in blacklist

import random

def generar_sopa_letras(palabras, filas=16, columnas=19):
    """
    Genera la matriz de la sopa de letras intentando maximizar
    los cruces entre palabras, y devuelve ubicaciones de cada palabra.
    """
    sopa = [['' for _ in range(columnas)] for _ in range(filas)]
    direcciones = [(0,1),(1,0),(0,-1),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
    ubicaciones = {}

    for palabra in palabras:
        p = palabra.upper()
        candidatos = []

        # 1) Explorar todas las posiciones posibles
        for df, dc in direcciones:
            for r0 in range(filas):
                for c0 in range(columnas):
                    rf = r0 + df*(len(p)-1)
                    cf = c0 + dc*(len(p)-1)
                    if not (0 <= rf < filas and 0 <= cf < columnas):
                        continue

                    # Comprobar si cabe y contar cruces
                    match_count = 0
                    ok = True
                    r, c = r0, c0
                    for l in p:
                        if sopa[r][c] == l:
                            match_count += 1
                        elif sopa[r][c] not in ('',):
                            ok = False
                            break
                        r += df; c += dc

                    if ok:
                        candidatos.append((match_count, r0, c0, df, dc))

        # 2) Si hay candidatos, elegir el que más cruces tenga
        if candidatos:
            # Orden descendente por match_count
            candidatos.sort(key=lambda x: x[0], reverse=True)
            _, r0, c0, df, dc = candidatos[0]

            # Colocar la palabra en la posición elegida
            r, c = r0, c0
            for l in p:
                sopa[r][c] = l
                r += df; c += dc

            rf, cf = r0 + df*(len(p)-1), c0 + dc*(len(p)-1)
            ubicaciones[p] = ((r0, c0), (rf, cf))

        else:
            # 3) Fallback: intento aleatorio breve
            intentos = 0
            placed = False
            while not placed and intentos < 200:
                intentos += 1
                df, dc = random.choice(direcciones)
                r0, c0 = random.randrange(filas), random.randrange(columnas)
                rf = r0 + df*(len(p)-1)
                cf = c0 + dc*(len(p)-1)
                if not (0 <= rf < filas and 0 <= cf < columnas):
                    continue

                ok = True
                r, c = r0, c0
                for l in p:
                    if sopa[r][c] not in ('', l):
                        ok = False
                        break
                    r += df; c += dc
                if not ok:
                    continue

                # Colocar en aleatorio
                r, c = r0, c0
                for l in p:
                    sopa[r][c] = l
                    r += df; c += dc
                ubicaciones[p] = ((r0, c0), (rf, cf))
                placed = True
            # Si tras el fallback no se coloca, se deja sin aparecer

    # 4) Rellenar espacios vacíos
    abecedario = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for i in range(filas):
        for j in range(columnas):
            if sopa[i][j] == '':
                sopa[i][j] = random.choice(abecedario)

    return sopa, ubicaciones

def dibujar_sopa(ax, sopa):
    """
    Draws only the outer border and letters of the word search with implicit cells.
    """
    filas, columnas = len(sopa), len(sopa[0])
    ax.axis('off')
    ax.set_xlim(0, columnas)
    ax.set_ylim(0, filas)
    ax.set_aspect('equal')
    # Draw only outer border
    ax.plot([0, columnas], [0, 0], color='black')
    ax.plot([columnas, columnas], [0, filas], color='black')
    ax.plot([columnas, 0], [filas, filas], color='black')
    ax.plot([0, 0], [filas, 0], color='black')
    # Place letters centered in each cell
    for i in range(filas):
        for j in range(columnas):
            ax.text(j + 0.5, filas - i - 0.5, sopa[i][j], va='center', ha='center', fontsize=12)

def crear_pdf(todos, nombre='100_sopas_letras.pdf'):
    """Generates PDF with puzzles containing word lists and solutions in 3 columns at the end, 3 puzzles per page."""
    with PdfPages(nombre) as pp:
        # Puzzle pages
        for idx, (sopa, palabras, _) in enumerate(todos):
            fig = plt.figure(figsize=(8.27, 11.69))
            # Puzzle title
            fig.text(
                0.5, 0.97,
                f"Sopa {idx+1} - {len(palabras)} palabras",
                ha='center', va='top', fontsize=14, weight='bold'
            )
            # Centered puzzle area with top and bottom margin for list
            # Área del puzzle centrado, dejando más espacio abajo para la lista
            # Área del puzzle centrado, dejando espacio amplio debajo para la lista
            ax = fig.add_axes([0.1, 0.35, 0.8, 0.5])
            dibujar_sopa(ax, sopa)
            # Word list below the puzzle in 4 columns
            cols = 4
            per_col = 10
            x_positions = [0.1 + i * 0.2 for i in range(cols)]
            y_start = 0.33
            y_step = 0.028
            for col in range(cols):
                for row in range(per_col):
                    idx_word = col * per_col + row
                    if idx_word >= len(palabras):
                        break
                    word = palabras[idx_word].upper()
                    fig.text(
                        x_positions[col],
                        y_start - row * y_step,
                        word,
                        va='top', ha='left', fontsize=10
                    )
            pp.savefig(fig)
            plt.close(fig)
                # Solution pages: show 10 solved puzzles per page with red highlights
        def dibujar_solucion(ax, sopa, ubic):
            # Draws the border and letters, and highlights words in red
            filas, columnas = len(sopa), len(sopa[0])
            ax.axis('off')
            ax.set_xlim(0, columnas)
            ax.set_ylim(0, filas)
            ax.set_aspect('equal')
            # Outer border
            ax.plot([0, columnas], [0, 0], color='black')
            ax.plot([columnas, columnas], [0, filas], color='black')
            ax.plot([columnas, 0], [filas, filas], color='black')
            ax.plot([0, 0], [filas, 0], color='black')
            # Letters
            for i in range(filas):
                for j in range(columnas):
                    ax.text(j + 0.5, filas - i - 0.5, sopa[i][j], va='center', ha='center', fontsize=8)
            # Highlight words
            for palabra, ((r0, c0), (rf, cf)) in ubic.items():
                # Calculate center points
                x0, y0 = c0 + 0.5, filas - r0 - 0.5
                x1, y1 = cf + 0.5, filas - rf - 0.5
                ax.plot([x0, x1], [y0, y1], color='red', linewidth=2)
        # Show 10 solutions per page
        per_page = 10
        n = len(todos)
        for start in range(0, n, per_page):
            fig = plt.figure(figsize=(8.27, 11.69))
            # Arrange in 2 columns x5 rows
            for idx in range(start, min(start + per_page, n)):
                sopa, _, ubic = todos[idx]
                loc = idx - start
                col = loc % 2
                row = loc // 2
                left = 0.05 + col * 0.475
                bottom = 0.05 + (4 - row) * 0.18
                width = 0.45
                height = 0.18
                ax = fig.add_axes([left, bottom, width, height])
                dibujar_solucion(ax, sopa, ubic)
                                # Left side title along the puzzle
                # usando coordenadas de ejes (fuera del borde)
                ax.text(
                    -0.1, 0.5,
                    f"Sopa {idx+1}",
                    va='center', ha='right', rotation=90,
                    fontsize=10, transform=ax.transAxes
                )
            pp.savefig(fig)
            plt.close(fig)
    print(f"PDF generado: {nombre}")


def crear_docx(todos, nombre='100_sopas_letras.docx'):
    """Generates DOCX with puzzles, list and highlighted solutions in mini-grids."""
    doc = Document()
    # Cover page
    doc.add_heading('Sopas de Letras', level=1)
    doc.add_page_break()
    # Puzzles with list
    for idx, (sopa, palabras, _) in enumerate(todos):
        # Insertar salto de página antes de cada sopa salvo la primera
        doc.add_heading(f'Sopa {idx+1} - {len(palabras)} palabras', level=2)
        # Puzzle
        fig = plt.figure(figsize=(6, 8))
        ax = fig.add_axes([0, 0, 1, 1])
        dibujar_sopa(ax, sopa)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        p = doc.add_paragraph()
        r = p.add_run()
        r.add_picture(buf, width=Inches(6))
        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        # Lista de palabras en 4 columnas
        table = doc.add_table(rows=10, cols=4)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        for i, w in enumerate(palabras):
            cell = table.rows[i % 10].cells[i // 10]
            cell.text = w.upper()
        # Solutions in 2x5 mini-grids per page with red highlights
    doc.add_heading('Soluciones', level=1)
    doc.add_page_break()
    per_page = 10
    for start in range(0, len(todos), per_page):
        group = todos[start:start+per_page]
        # tabla de 5 filas x 2 columnas para imágenes de solución
        table = doc.add_table(rows=5, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        for idx_in_group, entry in enumerate(group):
            sopa, _, ubic = entry
            # Render mini-grid with highlights
            fig = plt.figure(figsize=(3, 2.5))
            ax = fig.add_axes([0, 0, 1, 1])
            # dibujar solución
            filas, columnas = len(sopa), len(sopa[0])
            ax.axis('off'); ax.set_xlim(0, columnas); ax.set_ylim(0, filas); ax.set_aspect('equal')
            # borde exterior
            ax.plot([0, columnas], [0, 0], color='black')
            ax.plot([columnas, columnas], [0, filas], color='black')
            ax.plot([columnas, 0], [filas, filas], color='black')
            ax.plot([0, 0], [filas, 0], color='black')
            # letras
            for i in range(filas):
                for j in range(columnas):
                    ax.text(j+0.5, filas-i-0.5, sopa[i][j], va='center', ha='center', fontsize=6)
            # resaltar palabras
            for _, ((r0, c0), (rf, cf)) in ubic.items():
                x0, y0 = c0+0.5, filas-r0-0.5; x1, y1 = cf+0.5, filas-rf-0.5
                ax.plot([x0, x1], [y0, y1], color='red', linewidth=1)
            # título lateral
            ax.text(-0.1, 0.5, f"Sopa {start+idx_in_group+1}", va='center', ha='right', rotation=90, fontsize=8, transform=ax.transAxes)
            buf = io.BytesIO(); fig.savefig(buf, format='png', bbox_inches='tight'); plt.close(fig); buf.seek(0)
            # insertar en tabla
            row = idx_in_group // 2
            col = idx_in_group % 2
            cell = table.rows[row].cells[col]
            p = cell.paragraphs[0]
            run = p.add_run()
            run.add_picture(buf, width=Inches(2))
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER        
    doc.save(nombre)
    print(f"Word generado: {nombre}")

def main():
    # Prepare dictionary
    lista = top_n_list('es', 10000)
    print(f"Se obtuvieron las {len(lista)} palabras más comunes en español.")

    # Load blacklist from JSON file
    blacklist = cargar_blacklist_desde_json('blacklist.json')
    print(f"Se cargaron {len(blacklist)} palabras a la lista negra.")

    # Build dictionary excluding blacklist and length 4-10
    dic_filtrado = [w for w in lista if 4 <= len(w) <= 10 and w.isalpha() and es_palabra_permitida(w, blacklist)]
    print(f"Tamaño del diccionario original: {len(lista)} palabras.")
    print(f"Tamaño del diccionario filtrado (excluyendo blacklist y longitud): {len(dic_filtrado)} palabras.")

    # Generate puzzles ensuring 40 placed words and no repetition between puzzles
    todos = []
    used_global = set()
    total_sopas = 365
    print(f"\nComenzando la generación de {total_sopas} sopas de letras...")
    for idx in range(total_sopas):
        print(f"\nGenerando sopa de letras número {idx+1}...")
        available = [w for w in dic_filtrado if w.upper() not in used_global]
        print(f"  Palabras disponibles para esta sopa (no usadas previamente): {len(available)}.")
        if len(available) < 40:
            print("  No suficientes palabras nuevas disponibles. Reiniciando la lista de palabras usadas.")
            used_global.clear()
            available = dic_filtrado.copy()
            print(f"  Palabras disponibles después de reiniciar: {len(available)}.")
        if not available:
            print(f"  Advertencia: No hay suficientes palabras permitidas para generar la sopa {idx+1}. Saltando esta sopa.")
            continue
        seleccion = random.sample(available, min(40, len(available)))
        print(f"  Se seleccionaron {len(seleccion)} palabras para intentar colocar en esta sopa.")
        used_global.update(w.upper() for w in seleccion)
        sopa, ubicaciones = generar_sopa_letras(seleccion)
        colocadas = set(ubicaciones.keys())
        intentos_colocacion = 0
        while len(colocadas) < 40 and available and intentos_colocacion < 5000: # Añadimos un límite de intentos
            intentos_colocacion += 1
            faltan = 40 - len(colocadas)
            candidatos = [w for w in available if w.upper() not in colocadas]
            if not candidatos:
                print("  No se encontraron más candidatos para colocar.")
                break
            nuevas = random.sample(candidatos, min(faltan, len(candidatos)))
            print(f"  Intentando colocar {len(nuevas)} palabras adicionales (faltan {faltan}).")
            seleccion = [w for w in seleccion if w.upper() in colocadas] + nuevas
            sopa, ubicaciones = generar_sopa_letras(seleccion)
            nuevas_colocadas = set(ubicaciones.keys()) - colocadas
            colocadas = nuevas_colocadas.union(colocadas)
            print(f"  Número de palabras colocadas hasta ahora: {len(colocadas)}.")
            if len(colocadas) == 40:
                print("  Se lograron colocar 40 palabras en esta sopa.")
                break
        if len(colocadas) < 40:
            print(f"  Advertencia: No se pudieron colocar 40 palabras en la sopa {idx+1}. Se colocaron {len(colocadas)}.")
        todos.append((sopa, [w.upper() for w in seleccion], ubicaciones))

    print("\nGeneración de sopas de letras completada.")

    # Create files
    print("\nComenzando la creación del archivo PDF...")
    crear_pdf(todos)
    print("Creación del archivo PDF completada.")

    print("\nComenzando la creación del archivo DOCX...")
    crear_docx(todos)
    print("Creación del archivo DOCX completada.")

if __name__ == '__main__':
    main()

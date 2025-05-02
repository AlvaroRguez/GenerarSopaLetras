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

def generar_sopa_letras(palabras, filas=16, columnas=19):
    """
    Genera la matriz de la sopa de letras y devuelve ubicaciones de cada palabra.
    """
    sopa = [['' for _ in range(columnas)] for _ in range(filas)]
    direcciones = [(0,1),(1,0),(0,-1),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
    ubicaciones = {}
    for palabra in palabras:
        p = palabra.upper()
        colocado = False
        intentos = 0
        while not colocado and intentos < 1000:
            intentos += 1
            df, dc = random.choice(direcciones)
            r0, c0 = random.randrange(filas), random.randrange(columnas)
            rf, cf = r0 + df*(len(p)-1), c0 + dc*(len(p)-1)
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
            r, c = r0, c0
            for l in p:
                sopa[r][c] = l
                r += df; c += dc
            ubicaciones[p] = ((r0, c0), (rf, cf))
            colocado = True
        # Si no se coloca, será tratado más adelante
    # Rellenar espacios vacíos
    abecedario = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for i in range(filas):
        for j in range(columnas):
            if sopa[i][j] == '':
                sopa[i][j] = random.choice(abecedario)
    return sopa, ubicaciones


def dibujar_sopa(ax, sopa):
    """
    Dibuja solo el borde exterior y las letras de la sopa de letras con celdas implícitas.
    """
    filas, columnas = len(sopa), len(sopa[0])
    ax.axis('off')
    ax.set_xlim(0, columnas)
    ax.set_ylim(0, filas)
    ax.set_aspect('equal')
    # Dibujar solo borde exterior
    ax.plot([0, columnas], [0, 0], color='black')
    ax.plot([columnas, columnas], [0, filas], color='black')
    ax.plot([columnas, 0], [filas, filas], color='black')
    ax.plot([0, 0], [filas, 0], color='black')
    # Colocar letras centradas en cada celda
    for i in range(filas):
        for j in range(columnas):
            ax.text(j + 0.5, filas - i - 0.5, sopa[i][j], va='center', ha='center', fontsize=12)

def crear_pdf(todos, nombre='100_sopas_letras.pdf'):
    """Genera PDF con puzzles con lista de palabras y soluciones en 3 columnas al final, 3 sopas por página."""
    with PdfPages(nombre) as pp:
        # Páginas de puzzles
        for idx, (sopa, palabras, _) in enumerate(todos):
            fig = plt.figure(figsize=(8.27, 11.69))
            # Título de la sopa
            fig.text(
                0.5, 0.97,
                f"Sopa {idx+1} - {len(palabras)} palabras",
                ha='center', va='top', fontsize=14, weight='bold'
            )
            # Area del puzzle centrado con margen superior e inferior para lista
            # Área del puzzle centrado, dejando más espacio abajo para la lista
            # Área del puzzle centrado, dejando espacio amplio debajo para la lista
            ax = fig.add_axes([0.1, 0.35, 0.8, 0.5])
            dibujar_sopa(ax, sopa)
            # Lista de palabras bajo el puzzle en 4 columnas
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
                # Páginas de soluciones: mostrar 10 sopas resueltas por página con resaltado rojo
        def dibujar_solucion(ax, sopa, ubic):
            # Dibuja el borde y las letras, y rodea las palabras en rojo
            filas, columnas = len(sopa), len(sopa[0])
            ax.axis('off')
            ax.set_xlim(0, columnas)
            ax.set_ylim(0, filas)
            ax.set_aspect('equal')
            # Borde exterior
            ax.plot([0, columnas], [0, 0], color='black')
            ax.plot([columnas, columnas], [0, filas], color='black')
            ax.plot([columnas, 0], [filas, filas], color='black')
            ax.plot([0, 0], [filas, 0], color='black')
            # Letras
            for i in range(filas):
                for j in range(columnas):
                    ax.text(j + 0.5, filas - i - 0.5, sopa[i][j], va='center', ha='center', fontsize=8)
            # Resaltar palabras
            for palabra, ((r0, c0), (rf, cf)) in ubic.items():
                # calcular puntos centrales
                x0, y0 = c0 + 0.5, filas - r0 - 0.5
                x1, y1 = cf + 0.5, filas - rf - 0.5
                ax.plot([x0, x1], [y0, y1], color='red', linewidth=2)
        # Mostrar 10 soluciones por página
        per_page = 10
        n = len(todos)
        for start in range(0, n, per_page):
            fig = plt.figure(figsize=(8.27, 11.69))
            # organizar en 2 columnas x5 filas
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
                                # título lateral izquierdo a lo largo del puzzle
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
    """Genera DOCX con puzzles, lista y soluciones resaltadas en mini-cuadrículas."""
    doc = Document()
    # Portada
    doc.add_heading('Sopas de Letras', level=1)
    doc.add_page_break()
    # Puzzles con lista
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
        # Soluciones en mini-cuadrículas 2x5 por página con resaltado rojo
    doc.add_heading('Soluciones', level=1)
    per_page = 10
    for start in range(0, len(todos), per_page):
        group = todos[start:start+per_page]
        # tabla de 5 filas x 2 columnas para imágenes de solución
        table = doc.add_table(rows=5, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        for idx_in_group, entry in enumerate(group):
            sopa, _, ubic = entry
            # renderizar mini-cuadrícula con resaltado
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
    # Preparar diccionario
    lista = top_n_list('es', 10000)

    # Cargar la blacklist desde el archivo JSON
    blacklist = cargar_blacklist_desde_json('blacklist.json')
    print(f"Se cargaron {len(blacklist)} palabras a la lista negra.")

    # Construir diccionario excluyendo blacklist y longitud 4-10
    dic_filtrado = [w for w in lista if 4 <= len(w) <= 10 and w.isalpha() and es_palabra_permitida(w, blacklist)]
    print(f"Tamaño del diccionario original: {len(lista)}")
    print(f"Tamaño del diccionario filtrado (excluyendo blacklist): {len(dic_filtrado)}")

    # Generar sopas garantizando 40 colocadas y que palabras no se repitan entre sopas
    todos = []
    used_global = set()
    total_sopas = 10
    for idx in range(total_sopas):
        available = [w for w in dic_filtrado if w.upper() not in used_global]
        if len(available) < 40:
            used_global.clear()
            available = dic_filtrado.copy()
        if not available:
            print(f"Advertencia: No hay suficientes palabras permitidas para generar la sopa {idx+1}.")
            continue
        seleccion = random.sample(available, min(40, len(available)))
        used_global.update(w.upper() for w in seleccion)
        sopa, ubicaciones = generar_sopa_letras(seleccion)
        colocadas = set(ubicaciones.keys())
        while len(colocadas) < 40 and available:
            faltan = 40 - len(colocadas)
            candidatos = [w for w in available if w.upper() not in colocadas]
            if not candidatos:
                break
            nuevas = random.sample(candidatos, min(faltan, len(candidatos)))
            seleccion = [w for w in seleccion if w.upper() in colocadas] + nuevas
            sopa, ubicaciones = generar_sopa_letras(seleccion)
            colocadas = set(ubicaciones.keys())
        todos.append((sopa, [w.upper() for w in seleccion], ubicaciones))

    # Crear archivos
    crear_pdf(todos)
    crear_docx(todos)

if __name__ == '__main__':
    main()

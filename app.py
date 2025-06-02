from flask import Flask, render_template, request, session, redirect, url_for, send_file, flash
import os
from werkzeug.utils import secure_filename
import io
import matplotlib
matplotlib.use('Agg') # Use Agg backend for non-interactive plotting
import matplotlib.pyplot as plt
from config import (
    TOTAL_PUZZLES, WORDS_PER_PUZZLE, PUZZLE_ROWS, PUZZLE_COLUMNS,
    WORD_SOURCE as DEFAULT_WORD_SOURCE, # For logic within app.py
    WORD_SOURCE_FILE as DEFAULT_WORD_SOURCE_FILE, # For logic within app.py
    USE_LOOKFOR,
    # MAX_RAW_WORDS, MIN_WORD_LENGTH, MAX_WORD_LENGTH, POS_ALLOWED, DIRECTIONS, MAX_FALLBACK_TRIES
    # are no longer directly used by app.py for passing to generator/data_loader,
    # as those functions now handle their own defaults if None is passed.
)
from data_loader import get_raw_words, load_blacklist
from generator import build_filtered_dict, generate_word_search
from drawing import draw_puzzle, draw_solution # Assuming drawing.py exists
from export_docx import create_docx # Import for DOCX export

app = Flask(__name__)
app.secret_key = 'super secret key' # Needed for session management

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_route():
    # Get form data
    total_puzzles = int(request.form.get('total_puzzles', TOTAL_PUZZLES))
    words_per_puzzle = int(request.form.get('words_per_puzzle', WORDS_PER_PUZZLE))
    puzzle_rows = int(request.form.get('puzzle_rows', PUZZLE_ROWS))
    puzzle_columns = int(request.form.get('puzzle_columns', PUZZLE_COLUMNS))
    use_lookfor = request.form.get('use_lookfor') == 'true'

    # Handle file uploads
    word_source_file_path = None
    if 'word_source_file' in request.files and request.files['word_source_file'].filename != '':
        word_file = request.files['word_source_file']
        filename = secure_filename(word_file.filename)
        word_source_file_path = os.path.join('uploads', filename)
        word_file.save(word_source_file_path)
        print(f"Word source file uploaded: {word_source_file_path}")

    blacklist_file_path = None
    if 'blacklist_file' in request.files and request.files['blacklist_file'].filename != '':
        blacklist_file = request.files['blacklist_file']
        filename = secure_filename(blacklist_file.filename)
        blacklist_file_path = os.path.join('uploads', filename)
        blacklist_file.save(blacklist_file_path)
        print(f"Blacklist file uploaded: {blacklist_file_path}")

    # Placeholder for actual generation logic
    print(f"Received configuration:")
    print(f"  Total Puzzles: {total_puzzles}")
    print(f"  Words per Puzzle: {words_per_puzzle}")
    print(f"  Puzzle Rows: {puzzle_rows}")
    print(f"  Puzzle Columns: {puzzle_columns}")
    print(f"  Use Lookfor: {use_lookfor}")
    print(f"  Word Source File: {word_source_file_path}")
    print(f"  Blacklist File: {blacklist_file_path}")

    # Determine word_source_type for get_raw_words
    current_word_source_type = DEFAULT_WORD_SOURCE
    if word_source_file_path:
        current_word_source_type = "file"

    # --- Start of refactored generation logic with error handling ---
    try:
        # 1. Load words
        # max_raw_words could be a form field, for now, passing None to use default from data_loader
        raw_words = get_raw_words(
            word_source_file_path=word_source_file_path,
            word_source_type=current_word_source_type,
            max_raw_words=None # Or get from form: int(request.form.get('max_raw_words', SomeDefault))
        )
        if not raw_words:
            flash('Could not load any words. Please check word source or file.', 'error')
            if word_source_file_path and os.path.exists(word_source_file_path): os.remove(word_source_file_path)
            if blacklist_file_path and os.path.exists(blacklist_file_path): os.remove(blacklist_file_path)
            return redirect(url_for('home'))

        # 2. Load blacklist
        # load_blacklist will use its own default if blacklist_file_path is None
        blacklist_set = load_blacklist(blacklist_file_path=blacklist_file_path)

        # 3. Build filtered dictionary
        # min_word_length, max_word_length, pos_allowed could be form fields.
        # Passing None to use defaults from generator.py for now.
        # Note: build_filtered_dict in generator.py expects max_word_length as its 3rd param if min_word_length is also passed.
        # The refactored build_filtered_dict expects (raw, blacklist, min_word_length, max_word_length, pos_allowed)
        # The previous call was: build_filtered_dict(raw_words, blacklist, puzzle_columns, puzzle_rows)
        # This was incorrect based on typical build_filtered_dict usage (max_len usually relates to word length, not grid size).
        # Correcting to pass None for word length filters, letting generator use its defaults.
        filtered_dictionary = build_filtered_dict(
            raw=raw_words,
            blacklist=blacklist_set,
            min_word_length=None, # Or get from form: int(request.form.get('min_word_length', None))
            max_word_length=None, # Or get from form: int(request.form.get('max_word_length', None))
            pos_allowed=None      # Or get from form/config
        )

        if not filtered_dictionary:
            flash('No words suitable for puzzle generation after filtering. Try different words or criteria.', 'error')
            if word_source_file_path and os.path.exists(word_source_file_path): os.remove(word_source_file_path)
            if blacklist_file_path and os.path.exists(blacklist_file_path): os.remove(blacklist_file_path)
            return redirect(url_for('home'))

        # 4. Generate puzzles
        session['puzzles'] = [] # Initialize puzzles list in session
        generated_puzzles_count = 0

        for i in range(total_puzzles):
            print(f"Generating puzzle {i+1}...")
            # generate_word_search now expects:
            # (words, rows, columns, words_per_puzzle_target, use_lookfor, directions=None, max_fallback_tries=None)
            # The old call was: (filtered_dictionary, words_per_puzzle, puzzle_rows, puzzle_columns, use_lookfor_algorithm=use_lookfor)
            # Need to map words_per_puzzle to words_per_puzzle_target
            # And use_lookfor_algorithm to use_lookfor

            puzzle_result = generate_word_search(
                words=filtered_dictionary,
                rows=puzzle_rows,
                columns=puzzle_columns,
                words_per_puzzle_target=words_per_puzzle, # Mapped from form's words_per_puzzle
                use_lookfor=use_lookfor, # Mapped from form's use_lookfor
                directions=None, # Pass None to use default from generator's config
                max_fallback_tries=None # Pass None to use default from generator's config
            )

            if puzzle_result and puzzle_result[0]: # Check if puzzle_grid (first element of tuple) is not empty
                puzzle_grid, placed_words, locations = puzzle_result
                generated_puzzles_count += 1
                session['puzzles'].append({
                    'grid': puzzle_grid,
                    'words': placed_words,
                    'locations': locations,
                    'rows': puzzle_rows,
                    'columns': puzzle_columns
                })
                session.modified = True
                print(f"Puzzle {i+1} generated and stored in session.")
            else:
                print(f"Failed to generate puzzle {i+1}. Word list might be too challenging for the grid size/config.")
                # Optionally, flash a message here if a single puzzle fails but others might succeed

        if generated_puzzles_count == 0 and total_puzzles > 0 :
             flash(f'Could not generate any puzzles with the given words and configuration. Try a larger grid or simpler words.', 'warning')
             # Fall through to cleanup and redirect to home

    except FileNotFoundError as e:
        flash(f'Error: A required file was not found. {e}', 'error')
        return redirect(url_for('home'))
    except ValueError as e:
        flash(f'Error: Invalid value provided. {e}', 'error')
        return redirect(url_for('home'))
    except Exception as e:
        # General error catch
        print(f"An unexpected error occurred during puzzle generation: {e}") # Log for debugging
        flash(f'An unexpected error occurred: {e}. Please try again or check settings.', 'error')
        return redirect(url_for('home'))
    finally:
        # Clean up uploaded files regardless of success or failure within the try block
        if word_source_file_path and os.path.exists(word_source_file_path):
            try:
                os.remove(word_source_file_path)
                print(f"Cleaned up uploaded word source file: {word_source_file_path}")
            except Exception as e_clean:
                print(f"Error cleaning up word source file {word_source_file_path}: {e_clean}")
        if blacklist_file_path and os.path.exists(blacklist_file_path):
            try:
                os.remove(blacklist_file_path)
                print(f"Cleaned up uploaded blacklist file: {blacklist_file_path}")
            except Exception as e_clean:
                 print(f"Error cleaning up blacklist file {blacklist_file_path}: {e_clean}")

    if not session.get('puzzles'): # If list is empty after loop (no puzzles generated)
        flash('No puzzles were successfully generated. Please adjust your settings and try again.', 'warning')
        return redirect(url_for('home'))

    return redirect(url_for('show_puzzles_list'))

@app.route('/puzzles')
def show_puzzles_list():
    puzzles = session.get('puzzles', [])
    return render_template('preview_list.html', puzzles_count=len(puzzles))

@app.route('/preview/puzzle/<int:puzzle_index>')
def serve_puzzle_image(puzzle_index):
    puzzles = session.get('puzzles', [])
    if not puzzles or puzzle_index >= len(puzzles):
        return "Puzzle not found", 404

    puzzle_data = puzzles[puzzle_index]

    # Ensure grid is a list of lists of characters, not strings
    grid = puzzle_data['grid']
    if isinstance(grid, list) and all(isinstance(row, str) for row in grid):
        grid = [list(row) for row in grid]

    fig, ax = plt.subplots(figsize=(8, 8)) # Consider making figsize dynamic based on grid size

    # Draw the puzzle grid
    draw_puzzle(ax, grid)

    # Optionally, draw the solution if locations are available
    # For now, let's assume 'locations' might be empty or not present if solution drawing is not desired yet
    if 'locations' in puzzle_data and puzzle_data['locations']:
         # If you want to show solutions uncomment next line. For now, it's puzzle only.
        # draw_solution(ax, grid, puzzle_data['locations'])
        pass


    img_io = io.BytesIO()
    fig.savefig(img_io, format='png', bbox_inches='tight')
    plt.close(fig) # Close the figure to free memory
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')

@app.route('/export_docx')
def export_docx_route():
    puzzles_session_data = session.get('puzzles', [])
    if not puzzles_session_data:
        # Maybe flash a message or redirect to home with an error
        return redirect(url_for('home'))

    # Adapt session data to the format expected by create_docx:
    # list of tuples: [(puzzle_grid, placed_words, locations), ...]
    formatted_puzzles_data = []
    for p_data in puzzles_session_data:
        # Ensure grid is in the correct list-of-lists-of-chars format if it's not already
        grid = p_data['grid']
        if isinstance(grid, list) and all(isinstance(row, str) for row in grid):
            grid = [list(row) for row in grid]

        formatted_puzzles_data.append((
            grid,
            p_data['words'],
            p_data['locations']
        ))

    if not formatted_puzzles_data:
        return redirect(url_for('show_puzzles_list')) # Or home, with a message

    try:
        docx_io = create_docx(formatted_puzzles_data)
        return send_file(
            docx_io,
            as_attachment=True,
            download_name=f"{len(formatted_puzzles_data)}_word_search_puzzles.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        print(f"Error during DOCX export: {e}")
        # Potentially flash an error message to the user
        return redirect(url_for('show_puzzles_list'))


if __name__ == '__main__':
    app.run(debug=True)

import pytest
from app import app as flask_app # Assuming your Flask app instance is named 'app' in app.py
import os

@pytest.fixture
def app():
    # Setup for the Flask app, e.g., for testing config
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test_secret_key", # Important for session testing
        "WTF_CSRF_ENABLED": False # Disable CSRF for easier form testing if you were using Flask-WTF
    })
    # Create a temporary uploads folder if it doesn't exist for file upload tests
    # UPLOAD_FOLDER is not explicitly defined in app.py's config, but file uploads save to 'uploads'
    # So, we ensure this path relative to the app's root_path.
    upload_dir = os.path.join(flask_app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    flask_app.config['UPLOAD_FOLDER'] = upload_dir # Explicitly set for clarity if needed by tests

    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

def test_home_page(client):
    """Test the home page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Word Search Puzzle Generator" in response.data

def test_successful_puzzle_generation_redirects(client):
    """Test that successful puzzle generation redirects to the puzzle list page."""
    # Create a dummy word file in the uploads folder for the test
    # Using the UPLOAD_FOLDER from app config if available, or defaulting to 'uploads'
    upload_folder = client.application.config.get('UPLOAD_FOLDER', os.path.join(client.application.root_path, 'uploads'))
    os.makedirs(upload_folder, exist_ok=True) # Ensure it exists
    dummy_word_file_path = os.path.join(upload_folder, "dummy_words.txt")

    try:
        with open(dummy_word_file_path, "w") as f:
            f.write("PYTHON\nFLASK\nTEST")

        data = {
            'total_puzzles': '1',
            'words_per_puzzle': '2',
            'puzzle_rows': '10',
            'puzzle_columns': '10',
            # For this test, we are not uploading a file via the form submission here.
            # Instead, app.py's generate_route will use its default word source logic
            # if word_source_file_path is None.
            # If a file upload was strictly required by the route for this test path,
            # it would be: 'word_source_file': (open(dummy_word_file_path, 'rb'), 'dummy_words.txt')
            # However, the current app.py logic has a fallback for get_raw_words.
            # To make this test more robust for "default word source", we ensure no file is named in form.
        }
        # To test the default word source, we do not send 'word_source_file' in `data`.
        # The app.py logic: `current_word_source_type = DEFAULT_WORD_SOURCE` if `word_source_file_path` is None.
        # `get_raw_words` then uses `word_source_type` (which would be DEFAULT_WORD_SOURCE).
        # This assumes DEFAULT_WORD_SOURCE is 'wordfreq' or similar that doesn't require a file.
        # If DEFAULT_WORD_SOURCE is 'file' and DEFAULT_WORD_SOURCE_FILE is e.g. "words.txt", that file must exist.
        # For simplicity, let's assume the default setup works (e.g., wordfreq).

        response = client.post('/generate', data=data, content_type='multipart/form-data')

        assert response.status_code == 302 # Should redirect
        assert response.location == '/puzzles' # Should redirect to puzzle list

    finally: # Ensure cleanup
        # Clean up dummy file
        if os.path.exists(dummy_word_file_path):
            os.remove(dummy_word_file_path)

def test_generate_with_no_words_flashes_error(client):
    """Test that attempting to generate with no valid words (e.g., empty uploaded file) flashes an error."""
    upload_folder = client.application.config.get('UPLOAD_FOLDER', os.path.join(client.application.root_path, 'uploads'))
    os.makedirs(upload_folder, exist_ok=True) # Ensure it exists
    empty_file_path = os.path.join(upload_folder, "empty_words.txt")

    try:
        with open(empty_file_path, "w") as f:
            pass # Create empty file

        data = {
            'total_puzzles': '1',
            'words_per_puzzle': '1',
            'puzzle_rows': '10',
            'puzzle_columns': '10',
            'word_source_file': (open(empty_file_path, 'rb'), 'empty_words.txt')
        }

        response = client.post('/generate', data=data, content_type='multipart/form-data')

        assert response.status_code == 302 # Redirects back to home
        assert response.location == '/'

        # Check for flashed message
        with client.session_transaction() as sess:
            flashes = sess.get('_flashes', [])
            # print(f"Flashes: {flashes}") # For debugging if needed
            assert len(flashes) > 0
            # Check for a more specific message if possible, depends on app.py's flash messages
            assert any("Could not load any words" in message for category, message in flashes)
            # The original check was "Could not load any raw words", app.py uses "Could not load any words"

    finally: # Ensure cleanup
        # Clean up dummy file
        if os.path.exists(empty_file_path):
            os.remove(empty_file_path)

# Add more tests:
# - Test accessing /puzzles directly without generating (should show "No puzzles")
# - Test previewing a puzzle image (e.g., /preview/puzzle/0) after generation
# - Test exporting to DOCX
# - Test invalid form inputs (e.g., non-integer for rows)

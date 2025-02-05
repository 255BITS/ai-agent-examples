from flask import Flask, send_from_directory, redirect, abort
import os

app = Flask(__name__)

# Serve files from the core directory
@app.route('/core/<path:filename>')
def serve_core(filename):
    return send_from_directory('core', filename)

@app.route('/games/<path:filename>')
def serve_file(filename):
    # Construct the full paths for both directories
    games_path = os.path.join('games', filename)
    generated_path = os.path.join('generated', filename)

    # Check if the file exists in the 'games' directory first
    print("games", games_path, generated_path)
    if os.path.exists(games_path):
        return send_from_directory('games', filename)
    # If not found in 'games', check the 'generated' directory
    elif os.path.exists(generated_path):
        return send_from_directory('generated', filename)
    # If the file isn't found in either, return a 404 error
    else:
        abort(404)

if __name__ == '__main__':
    app.run(debug=True)

# Default route – redirect to the example Tic Tac Toe game
@app.route('/')
def index():
    return redirect('/games/example-tictactoe/index.html')

if __name__ == '__main__':
    # Run in debug mode for development
    app.run(debug=True)

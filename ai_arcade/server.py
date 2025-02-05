from flask import Flask, send_from_directory, redirect
import os

app = Flask(__name__)

# Serve files from the core directory
@app.route('/core/<path:filename>')
def serve_core(filename):
    return send_from_directory('core', filename)

# Serve files from the games directory
@app.route('/games/<path:filename>')
def serve_games(filename):
    return send_from_directory('games', filename)

# Default route – redirect to the example Tic Tac Toe game
@app.route('/')
def index():
    return redirect('/games/example-tictactoe/index.html')

if __name__ == '__main__':
    # Run in debug mode for development
    app.run(debug=True)

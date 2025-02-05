# AI-Generated Games with LLM

## TODO WIP this might not work right yet

This project is a toolkit for generating games using an AI agent powered by a Language Model (LLM). The AI agent reads your game specifications, designs a game based on your description, and generates the necessary files automatically.

## Overview

The project consists of several components that work together to facilitate the creation of games:

1. **Server**: Uses Flask (in server.py) to serve static game files and redirect users to a default example game.
2. **Core Modules**: 
   - **game_engine.js**: Provides a game loop with update and render functions that can be extended for custom game logic.
   - **dsl_parser.js**: Parses a simple DSL for game configurations.
   - **utils.js**: Contains utility functions for creating and manipulating DOM elements.
3. **AI Game Generator** (generate_game.py): 
   - Loads the project structure and its file contents (excluding the generated/ directory).
   - Accepts a game name and description as command-line arguments.
   - Interacts with the LLM to design the game by first calling the design_game tool with the complete game design and expected file list.
   - Uses the write_file tool to generate each file as specified by the design.

## Directory Structure

- **server.py**: Flask server that serves the core and game files.
       - Default route redirects to an example Tic Tac Toe game.
- **core/**: Contains shared modules.
   - game_engine.js, dsl_parser.js, utils.js.
- **generate_game.py**: AI agent that automates game generation through interaction with an LLM.
- **games/**: Contains example games.
   - *example-tictactoe*: A simple Tic Tac Toe game.
   - *example-breakout*: A Breakout game built using the game engine.

## How It Works

1. The server serves static assets from the **core** and **games** directories.
2. The AI agent in **generate_game.py** loads the current project files and sends them along with the game description to the LLM.
3. The LLM first calls the **design_game** tool to outline the complete design and generate a comma-separated list of expected file paths.
4. After design confirmation, the agent uses the **write_file** tool to create each file as described.
5. The process continues until all expected files are generated.

## Usage

To generate a new game, run the following command:

    ./generate_game.py <game_name> <description>

Make sure you have all necessary dependencies installed and that you run the script from the project root.

## License

This project is open source. See the LICENSE file for details.

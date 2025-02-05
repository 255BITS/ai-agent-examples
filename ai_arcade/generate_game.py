#!/usr/bin/env python3
"""
generate_game.py

Usage:
    generate_game.py <game_name> <description>

This agent:
  - Loads the entire project (all file contents, excluding the generated/ directory)
  - Takes the game name (first argument) and the game description (second argument)
  - Sends the full project details and design description to the LLM
  - Instructs the LLM to call the design_game tool (with a comma-separated list of expected file paths)
    before calling write_file.
  - Processes tool events as they come in. When a write_file event is received, the file is written immediately.
  - Updates the prompt to indicate which files still need to be generated.
  - Continues until the list of expected files is empty.
  
Note: The toolbox only supports primitive types (strings) so we use comma-delimited strings
for any list data.
"""

import os
import sys
from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter

def lm_call(prompt: str, system_prompt: str = "", model: str = "o3-mini") -> str:
    """
    Calls the model with the given prompt and returns the response.

    Args:
        prompt (str): The user prompt to send to the model.
        system_prompt (str, optional): The system prompt to send to the model. Defaults to "".
        model (str, optional): The model to use for the call.
        base_url (str, optional): The base URL of the API. Defaults to "https://api.deepseek.com".

    Returns:
        str: The response from the language model.
    """
    client = OpenAI()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    return response.choices[0].message.content

def load_project(root_dir):
    """
    Walk the project structure under root_dir and load all files (excluding generated/).
    Returns a dict mapping relative file paths to file contents.
    """
    project_files = {}
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip the generated folder if it exists.
        if 'generated' in dirnames:
            dirnames.remove('generated')
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(filepath, root_dir)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    project_files[relpath] = f.read()
            except Exception as e:
                print(f"Skipping {relpath}: {e}")
    return project_files

def main():
    if len(sys.argv) < 3:
        print("Usage: generate_game.py <game_name> <description>")
        sys.exit(1)
    game_name = sys.argv[1]
    description = sys.argv[2]

    # Load all project files (excluding generated/) and build a summary including full file contents.
    project_files = load_project(".")
    project_summary = ""
    for relpath, content in project_files.items():
        project_summary += f"File: {relpath}\n{content}\n\n"

    # pending_files will be set once the LLM calls design_game.
    pending_files = None  # This will be a set of file paths (strings)

    # Create the toolbox and supporting parser/formatter within main to capture local state.
    toolbox = Toolbox()
    parser = XMLParser(tag="use_tool")
    formatter = XMLPromptFormatter(tag="use_tool")

    # Tool: thinking
    def thinking(thoughts=""):
        print("[thinking] I'm thinking:", thoughts)

    toolbox.add_tool(
        name="thinking",
        fn=thinking,
        args={
            "thoughts": {"type": "string", "description": "Anything you want to think out loud"}
        },
        description="For thinking out loud"
    )

    # Tool: write_file
    def write_file(path, content):
        nonlocal pending_files
        base_dir = os.path.join("generated", game_name)
        full_path = os.path.join(base_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[write_file] Wrote file: {full_path}")
        # If pending_files is set, remove this file from the pending set.
        if pending_files is not None:
            file_trim = path.strip()
            if file_trim in pending_files:
                pending_files.remove(file_trim)
                print(f"[write_file] Removed '{file_trim}' from pending files.")

    toolbox.add_tool(
        name="write_file",
        fn=write_file,
        args={
            "path": {"type": "string", "description": "Relative file path (e.g., core/game_engine.js)"},
            "content": {"type": "string", "description": "Content of the file"}
        },
        description="Immediately write a file to the generated project"
    )

    # Tool: design_game
    def design_game(game_name_arg, description_arg, project_str, expected_files):
        nonlocal pending_files
        print(f"[design_game] Designing game '{game_name_arg}' with description:\n{description_arg}")
        print(f"[design_game] Received project contents (first 500 chars):\n{project_str[:500]}...")
        print(f"[design_game] Expected files (comma-delimited): {expected_files}")
        # Convert the comma-delimited expected_files string into a set.
        pending_files = set([f.strip() for f in expected_files.split(",") if f.strip()])
        print(f"[design_game] Pending files set to: {pending_files}")

    toolbox.add_tool(
        name="design_game",
        fn=design_game,
        args={
            "game_name": {"type": "string", "description": "Name of the game"},
            "description": {"type": "string", "description": "Game design description"},
            "project": {"type": "string", "description": "Comma-delimited list of project files with contents"},
            "expected_files": {"type": "string", "description": "Comma-delimited list of expected file paths"}
        },
        description="Design the new game before generating files; set the expected file list."
    )

    # Build the initial system prompt.
    system = (
        f"You are a game design AI agent. Your task is to design a new game called '{game_name}' "
        f"with the following description:\n\n{description}\n\n"
        "Below are all of the current project file contents:\n\n"
        f"{project_summary}\n"
        "IMPORTANT: Before writing any file, you must call the design_game tool with your complete design "
        "and provide a comma-separated list of expected file paths to be generated. Then, use write_file to create each file."
    )

    # Append tool usage instructions.
    system += "\n\n" + formatter.usage_prompt(toolbox)

    # Create an initial prompt.
    prompt = (
        f"Design the game '{game_name}' using the project details and description above. "
        "Remember: first call design_game with your design and list of expected files (comma-separated), "
        "then call write_file for each file you generate. If a file is not yet generated, include it in the expected_files list."
    )

    # Main loop: call the LLM and process events until all expected files have been generated.
    while True:
        response = llm_call(system_prompt=system, prompt=prompt)
        events = parser.parse(response)
        if not events:
            print("[main] No events returned by LLM, re-prompting...")
        for event in events:
            toolbox.use(event)

        # Update the system prompt with current pending files (if design_game has been called).
        if pending_files is not None:
            system = (
                f"You are a game design AI agent. Your task is to design a new game called '{game_name}' "
                f"with the following description:\n\n{description}\n\n"
                "Below are all of the current project file contents:\n\n"
                f"{project_summary}\n"
                "Remember: You must call design_game before writing any files with write_file.\n"
                f"Pending files to generate: {', '.join(sorted(pending_files))}\n"
            )
            system += "\n\n" + formatter.usage_prompt(toolbox)
        else:
            system = (
                f"You are a game design AI agent. Your task is to design a new game called '{game_name}' "
                f"with the following description:\n\n{description}\n\n"
                "Below are all of the current project file contents:\n\n"
                f"{project_summary}\n"
                "IMPORTANT: Before writing any file, call design_game with your complete design and a comma-separated "
                "list of expected file paths to be generated.\n"
            )
            system += "\n\n" + formatter.usage_prompt(toolbox)

        # If design_game has been called and all expected files have been written, we're done.
        if pending_files is not None and len(pending_files) == 0:
            print("[main] All expected files have been generated.")
            break

    print("[main] Game generation complete.")

if __name__ == "__main__":
    main()

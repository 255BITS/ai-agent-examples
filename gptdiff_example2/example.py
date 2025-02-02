----- ./README.md -----
# GPTDiff Example Project

Welcome to the GPTDiff Example Project! This repository demonstrates how to use GPTDiff's generate_diff and smartapply functions to automatically generate and apply code transformations.

In this example, the script (example.py) begins with a simple greeting function. The transformation goal is to rename the function "greet" to "welcome" and update its printed message from "Hello, world!" to "Welcome, world!". Running the script will showcase how GPTDiff processes a diff and safely applies changes to the code.

Before running the example, ensure that the gptdiff package is installed in your environment. Simply execute the example script as follows:
  
    ./example.py

Enjoy exploring the power of GPTDiff!

----- ./example.py -----
#!/usr/bin/env python3
from gptdiff import generate_diff, smartapply

def main():
    # Original codebase with a simple greeting function.
    files = {
        "example.py": "def greet():\n    print('Hello, world!')\n"
    }

    # Build the environment string by concatenating file paths and contents.
    env = ""
    for path, content in files.items():
        env += f"File: {path}\nContent:\n{content}\n"

    # Define the transformation goal:
    #   Rename function 'greet' to 'welcome'
    #   Change the printed message to 'Welcome, world!'
    goal = "Rename function 'greet' to 'welcome' and update the print message to 'Welcome, world!'"

    # Generate a unified git diff using GPTDiff.
    diff_text = generate_diff(environment=env, goal=goal)
    print("Generated Diff:")
    print(diff_text)

    # Apply the generated diff safely to the original files.
    updated_files = smartapply(diff_text, files)
    print("Updated file content for example.py:")
    print(updated_files["example.py"])

if __name__ == "__main__":
    main()
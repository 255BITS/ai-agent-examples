import os
from gptdiff import generate_diff, smartapply, build_environment

# This example codebase is defined as a dictionary, simulating files.
files = {
    "main.py": "def greet():\n    print('Hello, world!')\n"
}

# Our transformation goal: rename function 'greet' to 'welcome'
# and update the greeting message.
goal = "Rename function greet to welcome and update greeting message."

# Build an environment string from our current files.
env = build_environment(files)

# Use GPTDiff to generate a diff patch that implements our goal.
diff_patch = generate_diff(environment=env, goal=goal)
print("Generated diff patch:")
print(diff_patch)

# Now, apply the diff safely with smartapply. The API handles context,
# conflict resolution, and ensures the entire file is updated.
updated_files = smartapply(diff_patch, files)
print("\nUpdated main.py content:")
print(updated_files["main.py"])
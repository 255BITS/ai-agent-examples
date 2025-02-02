from gptdiff import generate_diff, smartapply
import os

def load_codebase():
    # Load the current codebase: here, the world.py file is the target for transformation.
    files = {}
    with open("world.py", "r") as f:
        files["world.py"] = f.read()
    return files

def build_environment(files):
    # Build an environment string that lists files and their content.
    env = ""
    for path, content in files.items():
        env += f"File: {path}\nContent:\n{content}\n"
    return env

def main():
    print("Starting synthetic world evolution simulation...")

    # Load initial codebase
    files = load_codebase()
    environment = build_environment(files)

    print("Generating diff to enhance world simulation...")
    # Generate a diff that modifies the evolve_world function to add resource boost and environmental events.
    diff_text = generate_diff(
        environment=environment,
        goal='Enhance evolve_world by increasing resources and adding a random environmental event after initial processing',
        model="o3-mini"
    )
    print("Generated diff:")
    print(diff_text)

    print("Applying diff using smartapply...")
    # Apply the diff transformation to our codebase safely.
    updated_files = smartapply(diff_text, files)

    # Write the updated code back to world.py
    with open("world.py", "w") as f:
        f.write(updated_files["world.py"])

    print("Transformed world.py content:")
    print(updated_files["world.py"])

if __name__ == "__main__":
    main()

# File: README.md
# Synthetic World Evolution
Welcome to the Synthetic World Evolution demo.

This project showcases how the AI-powered gptdiff API can evolve a synthetic world codebase.
Watch as our barren world transforms into a living, vibrant realm with each applied diff!

Usage:
  python world.py
  python evolve_diff.py

# File: evolve_diff.py
from gptdiff import generate_diff, smartapply

# Read current world state
with open("world.py", "r") as f:
    world_content = f.read()

# Build environment string for gptdiff
environment = f"File: world.py\nContent:\n{world_content}\n"

# Goal: Evolve the barren world into a vibrant ecosystem
print("Invoking generate_diff to evolve our world...")
diff_text = generate_diff(environment=environment, goal="Transform create_world function to evolve_world with a message about a vibrant world", model="deepseek-reasoner")

# Apply the generated diff using smartapply for safe transformation
updated_files = smartapply(diff_text, {"world.py": world_content})

# Write the updated world.py content back
with open("world.py", "w") as f:
    f.write(updated_files["world.py"])

print("Applied diff to world.py successfully!")
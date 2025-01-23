# story_refinement.py
import sys
import argparse
import asyncio
import re
from pathlib import Path
from ai_agent_toolbox import Toolbox, XMLParser
repo_root = Path(__file__).parent.parent
sys.path.append(str(repo_root))
from common.inference_engine import llm_call

# Shared components from storygen
BASE_EXPECTATIONS = """
Always maintain:
- Consistency with existing elements
- Natural flow and readability
- Appropriate tone and style
- Connection to the overall narrative
"""

NARRATIVE_FINISHER = {
    "name": "Elena Storyweaver",
    "role": "Narrative Completion Specialist",
    "system": f"""You are Elena Storyweaver, master of final story polish.
{BASE_EXPECTATIONS}

Focus on:
- Cohesive narrative voice
- Emotional resonance
- Thematic consistency
- Professional-grade prose

Important: Only make changes that elevate the work to publishable quality.
USER_INPUT
"""
}

current_story = None



async def polish_story(story: str, user_input: str, current_iteration: int,
                      max_iterations: int, previous_notes: list = None) -> tuple:
    parser = XMLParser(tag="use_tool")
    system_prompt = NARRATIVE_FINISHER["system"].replace("USER_INPUT", user_input)

    # Build iterative prompt
    prompt = f"Improve this story draft (iteration {current_iteration+1}/{max_iterations}):\n\n{story}"

    if previous_notes:
        notes_str = "\n".join([f"- Iteration {i+1}: {note}"
                             for i, note in enumerate(previous_notes)])
        prompt += f"\n\nPrevious refinement notes:\n{notes_str}"

    response = await llm_call(
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    # Extract any analysis notes from the response
    note_match = re.search(r"ANALYSIS NOTES:\n(.*?)\nSTORY:", response, re.DOTALL)
    story_content = re.sub(r"ANALYSIS NOTES:.*?STORY:", "", response, flags=re.DOTALL).strip()
    note = note_match.group(1).strip() if note_match else "No specific notes provided"

    return story_content, note

def refine_story(input_path: Path, output_path: Path, instruction: str, max_iterations: int = 3):
    with open(input_path) as f:
        story = f.read()

    change_log = []
    for i in range(max_iterations):
        print(f"Refinement iteration {i+1}/{max_iterations}")
        story, note = asyncio.run(
            polish_story(
                story,
                instruction,
                i,
                max_iterations,
                previous_notes=change_log if i > 0 else None
            )
        )
        change_log.append(note)

        # Save intermediate with notes
        with open(f"refinement_iteration_{i+1}.md", "w") as f:
            f.write(f"<!-- ITERATION {i+1} NOTES:\n{note}\n-->\n\n{story}")

    with open(output_path, "w") as f:
        f.write(f"<!-- FINAL REFINEMENT LOG:\n" + "\n".join(
            [f"Iteration {i+1}: {note}" for i, note in enumerate(change_log)]
        ) + "\n-->\n\n" + story)
    print(f"Final refined story saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Standalone story refinement pipeline')
    parser.add_argument('-i', '--input', type=Path, required=True,
                        help='Input story file (MD format)')
    parser.add_argument('-o', '--output', type=Path, default=Path('story_final.md'),
                        help='Output file path')
    parser.add_argument('-c', '--command', type=str, 
                        default="Apply professional editing polish while preserving story",
                        help='Refinement instructions for the AI')
    parser.add_argument('-m', '--max_iterations', type=int, default=3,
                        help='Number of refinement passes (default: 3)')
    
    args = parser.parse_args()
    
    if not args.input.exists():
        raise FileNotFoundError(f"Input file {args.input} not found")
    if args.max_iterations < 1:
        raise ValueError("Max iterations must be at least 1")
    
    refine_story(args.input, args.output, args.command, args.max_iterations)

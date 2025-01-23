# story_refinement.py
import sys
from pathlib import Path
import argparse
import asyncio
import re
from datetime import datetime
from pathlib import Path
from ai_agent_toolbox import Toolbox, XMLParser
from ai_agent_toolbox import XMLPromptFormatter

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

def create_toolbox():
    toolbox = Toolbox()
    refinement_notes = []

    def add_notes(note: str):
        nonlocal refinement_notes
        refinement_notes.append(note)
        return "Notes added."

    toolbox.add_tool(
        name="add_notes",
        fn=add_notes,
        args={
            "note": {
                "type": str,
                "description": "Notes from the refinement process. This should contain analysis of changes made and suggestions for further improvements."
            }
        },
        description="Adds notes to the refinement log. Use this to provide analysis of changes and suggest further improvements in each iteration."
    )
    toolbox.refinement_notes = refinement_notes # Attach notes list to toolbox for access later
    return toolbox


async def polish_story(notes: str, story: str, model_name: str, user_input: str, current_iteration: int,
                      max_iterations: int, previous_notes: list = None) -> tuple:
    parser = XMLParser(tag="use_tool")
    formatter = XMLPromptFormatter(tag="use_tool")
    toolbox = create_toolbox() # Create toolbox for each iteration to reset notes
    global current_story
    current_story = story # make story accessible to tools if needed, though add_notes doesnt use it.

    tool_prompt = formatter.usage_prompt(toolbox)

    system_prompt = NARRATIVE_FINISHER["system"].replace("USER_INPUT", user_input)

    # Build iterative prompt
    prompt = f"Write this as a short story draft. Don't copy sections, instead pull from the sections as needed to make it compelling yet accessible. Iteration (iteration {current_iteration+1}/{max_iterations}):\n\n"
    prompt += f"Notes:\n{notes}"
    if notes != story:
        prompt += f"\nCurrent Story(modify this):\n{story}"

    if previous_notes:
        notes_str = "\n".join([f"- Iteration {i+1}: {note}"
                             for i, note in enumerate(previous_notes)])
        prompt += f"\n\nPrevious refinement notes:\n{notes_str}\n\n Please use the <use_tool><name>add_notes</name>...</use_tool> tag to provide analysis notes."

    print("SYSTEM", system_prompt)
    print("PROMPT", prompt+"\n\n"+ tool_prompt)

    response = await llm_call(
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": prompt + "\n\n" + tool_prompt
        }],
        model_name=model_name
    )

    story_content = response.strip() # story is the full response now, tool call will be parsed out
    notes_added = []
    for event in parser.parse(response):
        if event.is_tool_call:
            notes_added = toolbox.use(event)  # Returns list of added notes
    iteration_notes = notes_added[-1] if notes_added else ""

    return story_content, iteration_notes

def refine_story(input_path: Path, output_path: Path, instruction: str, max_iterations: int = 3):
    with open(input_path, encoding='utf-8') as f:
        story = f.read()

    change_log = []
    original_notes = story

    for i in range(max_iterations):
        print(f"Refinement iteration {i+1}/{max_iterations}")
        refined_story, note = asyncio.run(
            polish_story(
                original_notes,
                story,
                args.model, # Pass model here
                instruction,
                i,
                max_iterations,
                previous_notes=change_log if i > 0 else None,
            )
        )
        story = refined_story # update story for next iteration
        change_log.append(note)

        # Save intermediate with notes
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        Path("working").mkdir(parents=True, exist_ok=True)
        intermediate_file = f"working/{output_path.stem}_iter{i+1}_{timestamp}.md"
        with open(intermediate_file, "w") as f:
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
    parser.add_argument('--model', type=str, default='gemini-2.0-flash-thinking-exp-01-21',
                        help='LLM model to use for inference')

    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Input file {args.input} not found")
    if args.max_iterations < 1:
        raise ValueError("Max iterations must be at least 1")

    refine_story(args.input, args.output, args.command, args.max_iterations)

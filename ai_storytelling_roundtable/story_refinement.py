# story_refinement.py
import sys
from pathlib import Path
import argparse
import asyncio
import contextvars
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

# Context-based state management
current_story_context = contextvars.ContextVar('current_story', default='')
refinement_notes_context = contextvars.ContextVar('refinement_notes', default=[])

def create_toolbox():
    toolbox = Toolbox()
    
    def add_notes(note: str):
        notes = refinement_notes_context.get().copy()
        notes.append(note)
        refinement_notes_context.set(notes)
        print("NOTE", note)
        return note  # Return actual note content instead of confirmation

    toolbox.add_tool(
        name="add_notes",
        fn=add_notes,
        args={
            "note": {
                "type": "string",
                "description": "Complete analysis of changes and suggestions as a single coherent note."
            }
        },
        description="Adds notes to the refinement log. Use this to provide analysis of changes and suggest further improvements in each iteration."
    )
    return toolbox

async def polish_story(notes: str, story: str, model_name: str, user_input: str, current_iteration: int,
                      max_iterations: int, previous_notes: list = None) -> tuple[str, str]:
    # Debug logging for input tracking
    print(f"\n[DEBUG] Starting iteration {current_iteration+1}")
    print(f"[DEBUG] Notes length: {len(notes)}, Story length: {len(story)}")
    
    parser = XMLParser(tag="use_tool") 
    formatter = XMLPromptFormatter(tag="use_tool") 
    toolbox = create_toolbox() # Create toolbox for each iteration to reset notes
    refinement_notes_context.set([])  # Reset notes for this iteration
    current_story_context.set(story)  # Set story in context
    
    tool_prompt = formatter.usage_prompt(toolbox)

    system_prompt = NARRATIVE_FINISHER["system"].replace("USER_INPUT", user_input)

    # Build iterative prompt
    prompt = [
        f"REFINE CURRENT STORY DRAFT. Iteration ({current_iteration+1}/{max_iterations}):",
        "\n[INSTRUCTIONS] Apply these notes to improve the story:",
        notes if notes else "No previous notes",
        "\n\n[WORKING DRAFT] Modify THIS story version:",
        f"{story}"
    ]

    if previous_notes:
        prompt.append("\n\n[REFINEMENT HISTORY]")
        prompt.extend(f"- Iter {i+1}: {n[:200]}..." for i, n in enumerate(previous_notes))

    full_prompt = "\n".join(prompt)
    print(f"[PROMPT STRUCTURE]\nInstruction: {user_input}\nChars: {len(prompt)}")
    
    response = await llm_call(
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": full_prompt + "\n\n" + tool_prompt
        }],
        model_name=model_name
    )

    print(f"[DEBUG] Response length: {len(response)} chars")
    print("RESPONSE", response)

    story_content = response.strip() # story is the full response now, tool call will be parsed out
    notes_added = []
    for event in parser.parse(response):
        if event.is_tool_call:
            notes_added.append(toolbox.use(event))  # Preserve complete notes as single entries
    iteration_notes = " ".join(notes_added) if notes_added else ""
    
    print(f"[DEBUG] Iteration complete. New story length: {len(story_content)}")

    return story_content, iteration_notes

def refine_story(input_path: Path, output_path: Path, instruction: str, max_iterations: int = 3):
    with open(input_path, encoding='utf-8') as f:
        original_story = f.read()
    story = "Nothing yet"

    change_log = []  # Track refinement notes between iterations

    print(f"\n[INITIAL INPUT] Story length: {len(story)} chars")

    for i in range(max_iterations):
        print(f"Refinement iteration {i+1}/{max_iterations}")
        refined_story, note = asyncio.run(
            polish_story(  # Toolbox now properly captures full notes
                original_story,  # Pass accumulated notes
                story,
                args.model, # Pass model here
                instruction,
                i,
                max_iterations,
                previous_notes=change_log if i > 0 else None,
            )
        )
        story = refined_story  # Update story for next iteration
        change_log.append(note)

        # Save intermediate with notes
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        Path("working").mkdir(parents=True, exist_ok=True)
        intermediate_file = f"working/{output_path.stem}_iter{i+1}_{timestamp}.md"  # Unified note format
        with open(intermediate_file, "w") as f:
            f.write(f"<!-- ITERATION {i+1} NOTES:\n{note}\n-->\n\n{story}")

    with open(output_path, "w") as f:
        f.write(story+f"\n\n<!-- FINAL REFINEMENT LOG:\n" + "\n".join(
            [f"Iteration {i+1}: {note}" for i, note in enumerate(change_log)]
        ) + "\n-->")
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

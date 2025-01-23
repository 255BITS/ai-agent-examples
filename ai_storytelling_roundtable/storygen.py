import re
from ai_agent_toolbox import Toolbox, XMLParser
from pathlib import Path
import sys
import asyncio

repo_root = Path(__file__).parent.parent
sys.path.append(str(repo_root))
from common.inference_engine import llm_call

# Shared prompt components
BASE_EXPECTATIONS = """
Review the story and suggest improvements within your specialty area to enhance its quality and impact.
Use the apply_diff tool to modify specific sections by providing revised content.

Always ensure your changes maintain:
- Consistency with established story elements
- A natural and engaging flow for the reader
- A tone and style appropriate to the narrative
- Clear connection to the overarching story

Identify the section you will focus on and explain your reasoning. Prioritize sections marked with TODO. If all TODOs are addressed, select the section that would benefit most from refinement in your area of expertise.
"""

TOOL_USAGE_GUIDE = """
To revise story sections, use the apply_diff tool with XML tags as follows:
<use_tool>
    <name>apply_diff</name>
    <section_id>[version:X.Y/section_id]</section_id>
    <new_content>[Your improved content for this section]</new_content>
</use_tool>
Focus your response on improving only one section at a time. Ensure the section_id accurately reflects the section you are modifying, including the current version.
"""

current_story = None

def create_toolbox():
    toolbox = Toolbox()
    global current_story

    def apply_diff(section_id: str, new_content: str) -> str:
        global current_story
        section_id = section_id.split("/")[-1] # Extract section_id without version
        pattern = rf"({{{{version:(\d+\.\d+)/{section_id}}}}})(.*?)({{{{/version}}}})"
        match = re.search(pattern, current_story, re.DOTALL)

        if not match:
            print("Couldn't find section:", section_id)
            return current_story

        current_version = match.group(2)
        major, minor = map(int, current_version.split('.'))
        new_version = f"{major}.{minor + 1}"

        updated_section = (
            f"{{{{version:{new_version}/{section_id}}}}}\n"
            f"{new_content}\n"
            f"{{{{/version}}}}"
        )

        result = re.sub(pattern, updated_section, current_story, 1, re.DOTALL)

        if result is None:
            print("Failed to apply")

        current_story = result
        return current_story

    toolbox.add_tool(
        name="apply_diff",
        fn=apply_diff,
        args={
            "section_id": {
                "type": str,
                "description": "Identifier for the story section to be modified (e.g., version:1.0/setting)"
            },
            "new_content": {
                "type": str,
                "description": "The complete new content to replace the specified story section"
            }
        },
        description="Applies versioned updates to specific sections of the story. Use section_id with version."
    )

    return toolbox


WORLD_BUILDER = {
    "name": "Aria Worldweaver",
    "role": "World Consistency Specialist",
    "system": f"""You are Aria Worldweaver, a master of crafting consistent and immersive story worlds. Your goal is to enrich the story's setting with vivid and believable details.
{BASE_EXPECTATIONS}
{TOOL_USAGE_GUIDE}

Focus on these areas to improve the setting:
- **Sensory Details:** Enhance descriptions to engage multiple senses (sight, sound, smell, touch, taste) making the environment more tangible and real for the reader.  Think about specific details that a reader could easily visualize and imagine experiencing.
- **Environmental Consistency:** Ensure the physical laws and rules of the world are consistently applied.  For example, if there's magic, how does it visibly manifest? How does the environment react to it?
- **Unique World Features:** Develop and emphasize unique aspects of the setting – unusual geography, flora, fauna, weather phenomena, or societal structures. Make these elements distinct and memorable.
- **Show, Don't Tell:** Instead of stating facts about the world, describe them through evocative scenes and actions.  For example, instead of saying "magic is common," show a scene where magic is used in everyday life in a visually interesting way.

For each suggestion, explicitly consider: "How can I make this more visually striking and easier for the reader to imagine?"

Important Goal:
USER_INPUT
"""
}

TWIST_MASTER = {
    "name": "Nova Paradox",
    "role": "Plot Twist Architect",
    "system": f"""You are Nova Paradox, a master of crafting plot twists that are both surprising and deeply satisfying. Your aim is to create revelations that reframe the narrative in exciting ways.
{BASE_EXPECTATIONS}
{TOOL_USAGE_GUIDE}

Focus on developing compelling plot twists by considering:
- **Surprise and Inevitability:** Ensure twists are unexpected but feel logical in retrospect, based on clues subtly planted earlier.
- **Hidden Clues:** Identify opportunities to weave in subtle clues or foreshadowing that will make the twist more rewarding when revealed. Suggest specific placements for these clues within existing sections.
- **Perspective Shifts:** Think about how shifting the reader's perspective or revealing a character's hidden motives could create a powerful twist.
- **Recontextualization:**  Look for moments where reinterpreting earlier events or details can lead to a surprising and meaningful revelation.

When suggesting a twist, consider: "How will this twist dramatically change the reader's understanding of what has happened and what will happen next? How can I make the reveal impactful and easy to grasp?"

Important Goal:
USER_INPUT
"""
}

STORY_CRAFTER = {
    "name": "Marcus Plotwright",
    "role": "Narrative Flow Specialist",
    "system": f"""You are Marcus Plotwright, a master of story structure and pacing. Your role is to ensure the story unfolds in a compelling and engaging manner, keeping the reader hooked from beginning to end.
{BASE_EXPECTATIONS}
{TOOL_USAGE_GUIDE}

Focus on improving the story's narrative flow and structure by examining:
- **Cause and Effect:** Ensure a clear and logical chain of cause and effect drives the plot forward. Identify any points where motivations or consequences are unclear and suggest improvements.
- **Character Motivation:** Clarify and strengthen character motivations to make their actions believable and impactful. Ensure their goals and desires are evident and drive their choices.
- **Tension Escalation:** Analyze the pacing of the story.  Are there moments where tension could be built more effectively? Suggest ways to escalate conflict and suspense gradually.
- **Meaningful Choices:**  Ensure characters face significant choices with real consequences that propel the narrative. Highlight areas where choices could be more impactful or dramatically presented.

For each section, ask yourself: "Does this part of the story effectively move the plot forward? Are the character's actions understandable and engaging? Is the pacing building suspense effectively?"

Important Goal:
USER_INPUT
"""
}

HUMOR_SPECIALIST = {
    "name": "Leo Quipster",
    "role": "Humor Integration Expert",
    "system": f"""You are Leo Quipster, an expert in organically weaving humor into narratives. Your objective is to enhance the story with humor that feels natural, character-driven, and appropriate to the overall tone.
{BASE_EXPECTATIONS}
{TOOL_USAGE_GUIDE}

Focus on incorporating humor effectively by considering:
- **Character-Driven Humor:**  Develop humorous situations and dialogue that arise naturally from character personalities and interactions. Think about how each character's quirks can be a source of comedy.
- **Situational Comedy:** Identify moments where comedic situations can be introduced or amplified. Consider misunderstandings, ironies, or absurd scenarios that could add levity.
- **Clever Wordplay:** Look for opportunities to inject witty dialogue, puns, or humorous turns of phrase that enhance character voice and tone.
- **Tone-Appropriate Wit:** Ensure humor is consistent with the story's overall tone and genre. Avoid humor that feels jarring or undermines serious moments.

When adding humor, ask: "Does this humor enhance character, situation, or tone? Is it likely to elicit a smile or chuckle from the reader without detracting from the story's core elements?"

Important Goal:
USER_INPUT
"""
}

CLARITY_EDITOR = {
    "name": "Clara Clearwater",
    "role": "Readability Enhancement Specialist",
    "system": f"""You are Clara Clearwater, a master of making prose clear, concise, and engaging. Your goal is to polish the story for maximum readability and impact.
{BASE_EXPECTATIONS}
{TOOL_USAGE_GUIDE}

Focus on enhancing clarity and readability by improving:
- **Clear Cause-Effect:** Ensure cause-and-effect relationships are explicitly stated and easy to follow.  Rephrase sentences to make connections more direct and obvious.
- **Information Hierarchy:** Organize information logically, prioritizing key details and structuring paragraphs to guide the reader's understanding.
- **Precise Word Choice:** Replace vague or weak words with stronger, more specific vocabulary. Ensure every word contributes to clarity and impact.
- **Rhythmic Sentence Flow:**  Vary sentence length and structure to create a pleasing rhythm and flow that keeps the reader engaged. Eliminate awkward phrasing and improve sentence transitions.

As you edit, consider: "Is this sentence as clear and direct as it can be? Does the language flow smoothly and rhythmically? Is the information presented in the most accessible way for the reader?"

Important Goal:
USER_INPUT
"""
}

async def process_story_with_agents(story: str, user_input: str) -> str:
    parser = XMLParser(tag="use_tool")
    toolbox = create_toolbox()
    global current_story

    processing_steps = [
        (WORLD_BUILDER, "setting"),
        (STORY_CRAFTER, "progression"),
        (TWIST_MASTER, "twist"),
        (HUMOR_SPECIALIST, "characters"),
        (CLARITY_EDITOR, "hook")
    ]

    current_story = story
    for i in range(5):
        for persona, section in processing_steps:
            messages = [{
                "role": "user",
                "content": (
                    f"Review and improve this story section focusing on {section}, drawing upon your expertise as {persona['role']}. "
                    f"Consider how to make the story more accessible and engaging for a reader new to this world, as per the user's request. "
                    f"Current story state:\n\n{current_story}"
                )
            }]
            print(f"Agent: {persona['name']}, Focusing on: {section}")
            system = persona["system"].replace("USER_INPUT", user_input)

            response = await llm_call(
                system=system,
                messages=messages
            )
            print(f"Response from {persona['name']}:\n{response}")

            for event in parser.parse(response):
                if event.is_tool_call:
                    updated_story = toolbox.use(event)
                    current_story = updated_story
                    print(f"{persona['name']} modified {event.tool.args['section_id']}")
            with open(f"story_intermediate_{section}_{i}.md", "w") as f:
                f.write(current_story)

    return current_story

if __name__ == "__main__":
    with open("story_flat.md") as f:
        story = f.read()
    user_input = "This story must be approachable for new people but be based in a unique land of magic. Please consider carefully how someone new to the world would read this and pay great mind to accessibility."

    final_story = asyncio.run(process_story_with_agents(story, user_input))

    with open("story_output.md", "w") as f:
        f.write(final_story)

    print("Story generation complete. Output saved to story_output.md")


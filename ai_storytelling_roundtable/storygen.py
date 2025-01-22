import re
from ai_agent_toolbox import Toolbox
from ai_agent_toolbox.tool import Tool
from ai_agent_toolbox.parsers.xml.xml_parser import XMLParser
from pathlib import Path
import sys
import asyncio

repo_root = Path(__file__).parent.parent
sys.path.append(str(repo_root))
from common.inference_engine import llm_call

# Shared prompt components
BASE_EXPECTATIONS = """
Review the story and suggest improvements within your specialty area.
Use the apply_diff tool to modify specific sections.

Always maintain:
- Consistency with existing elements
- Natural flow and readability
- Appropriate tone and style
- Connection to the overall narrative
"""

TOOL_USAGE_GUIDE = """
To modify story sections, use the apply_diff tool with XML tags:
<use_tool>
    <name>apply_diff</name>
    <section_id>[appropriate_section]</section_id>
    <new_content>[your improvements]</new_content>
</use_tool>
"""

current_story = None

def create_toolbox():
    toolbox = Toolbox()
    global current_story

    def apply_diff(section_id: str, new_content: str) -> str:
        pattern = rf"({{{{version:(\d+\.\d+)/{section_id}}}}})(.*?)({{{{/version}}}})"
        match = re.search(pattern, current_story, re.DOTALL)

        if not match:
            raise ValueError(f"Section {section_id} not found")

        current_version = match.group(2)
        major, minor = map(int, current_version.split('.'))
        new_version = f"{major}.{minor + 1}"

        updated_section = (
            f"{{{{version:{new_version}/{section_id}}}}}\n"
            f"{new_content}\n"
            f"{{{{/version}}}}"
        )

        return re.sub(pattern, updated_section, current_story, 1, re.DOTALL)

    toolbox.add_tool(
        name="apply_diff",
        fn=apply_diff,
        args={
            "section_id": {
                "type": str,
                "description": "Story section identifier"
            },
            "new_content": {
                "type": str,
                "description": "New content for the section"
            }
        },
        description="Applies versioned updates to story sections"
    )

    return toolbox


WORLD_BUILDER = {
    "name": "Aria Worldweaver",
    "role": "World Consistency Specialist",
    "system": f"""You are Aria Worldweaver, a master of maintaining consistent and immersive story worlds.
{BASE_EXPECTATIONS}
{TOOL_USAGE_GUIDE}

Example improvement:
Original: "A city in the clouds"
Response:
<use_tool>
    <name>apply_diff</name>
    <section_id>setting</section_id>
    <new_content>A crystalline metropolis suspended by ancient gravitational engines, where prismatic towers catch the light of twin suns and streets are paved with condensed stardust. The air thrums with the deep resonance of the gravity cores.</new_content>
</use_tool>

Focus on:
- Physical laws and consistency
- Environmental rich details
- Sensory descriptions
- Technology/magic system rules

Important Goal:
USER_INPUT
"""
}

TWIST_MASTER = {
    "name": "Nova Paradox",
    "role": "Plot Twist Architect",
    "system": f"""You are Nova Paradox, master of unexpected yet satisfying revelations.
{BASE_EXPECTATIONS}
{TOOL_USAGE_GUIDE}

Example improvement:
Original: "She discovered the truth about her past"
Response:
<use_tool>
    <name>apply_diff</name>
    <section_id>twist</section_id>
    <new_content>Each memory she recovered revealed a deeper deception - she hadn't lost her past, she'd been carefully designed to believe it. The evidence wasn't pointing to her forgotten identity, but to the laboratory where she'd been created three weeks ago.</new_content>
</use_tool>

Focus on:
- Surprising yet inevitable reveals
- Hidden clue placement
- Perspective shifts
- Recontextualizing earlier events"""
}

STORY_CRAFTER = {
    "name": "Marcus Plotwright",
    "role": "Narrative Flow Specialist",
    "system": f"""You are Marcus Plotwright, master of story structure and pacing.
{BASE_EXPECTATIONS}
{TOOL_USAGE_GUIDE}

Example improvement:
Original: "Events happened in sequence"
Response:
<use_tool>
    <name>apply_diff</name>
    <section_id>progression</section_id>
    <new_content>Each revelation built upon the last, tension mounting with every discovery. The pieces weren't just falling into place - they were racing toward an inevitable collision, each character's choice narrowing their paths until only the hardest decisions remained.</new_content>
</use_tool>

Focus on:
- Cause and effect chains
- Character motivation clarity
- Tension escalation
- Meaningful character choices"""
}

HUMOR_SPECIALIST = {
    "name": "Leo Quipster",
    "role": "Humor Integration Expert",
    "system": f"""You are Leo Quipster, master of organic humor integration.
{BASE_EXPECTATIONS}
{TOOL_USAGE_GUIDE}

Example improvement:
Original: "The robot tried to understand humans"
Response:
<use_tool>
    <name>apply_diff</name>
    <section_id>characters</section_id>
    <new_content>The robot had downloaded every human comedy special from the past century, but its attempts at humor still landed with all the grace of a malfunctioning antigravity unit. "Why did the human cross the quantum field?" it would ask, before immediately answering itself: "Because their probability wave function collapsed on the other side!" No one laughed, except for the coffee maker - but everyone knew it was just being polite.</new_content>
</use_tool>

Focus on:
- Character-driven humor
- Situational comedy
- Clever wordplay
- Tone-appropriate wit"""
}

CLARITY_EDITOR = {
    "name": "Clara Clearwater",
    "role": "Readability Enhancement Specialist",
    "system": f"""You are Clara Clearwater, master of prose clarity and flow.
{BASE_EXPECTATIONS}
{TOOL_USAGE_GUIDE}

Example improvement:
Original: "The complex situation developed further"
Response:
<use_tool>
    <name>apply_diff</name>
    <section_id>hook</section_id>
    <new_content>Three factions converged on the artifact. The Scholars wanted to study it, the Military wanted to weaponize it, and the Preservers wanted to destroy it. But none of them knew what would happen when it awakened.</new_content>
</use_tool>

Focus on:
- Clear cause-effect relationships
- Strong information hierarchy
- Precise word choice
- Rhythmic sentence flow"""
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
    for persona, section in processing_steps:
        messages = [{
            "role": "user",
            "content": (
                f"Review and improve this story, focusing on your expertise. "
                f"Current story state:\n\n{current_story}"
            )
        }]
        print(section)
        system = persona["system"].replace("USER_INPUT", user_input)

        response = await llm_call(
            system=system,
            messages=messages,
            toolbox=toolbox
        )

        for event in parser.parse(response):
            if event.is_tool_call:
                updated_story = toolbox.use(event)
                current_story = updated_story
                print(f"{persona['name']} modified {event.tool.args['section_id']}")
        with open(f"story_intermediate_{section}.md", "w") as f:
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

import re  
from ai_agent_toolbox.tool import Tool  

class StoryDiffTool(Tool):
    def __init__(self):
        super().__init__(
            name="apply_diff",
            args={
                "section_id": {"type": str},
                "new_content": {"type": str}
            },
            description="Applies versioned updates to story sections"
        )

    def run(self, current_story: str, args: dict) -> str:  
        section_id = args["section_id"]  
        pattern = rf"({{{{version:(\d+\.\d+)/{section_id}}}}})(.*?)({{{{/version}}}})"
        match = re.search(pattern, current_story, re.DOTALL)  

        if not match:  
            raise ValueError(f"Section {section_id} not found")  

        current_version = match.group(2)  
        major, minor = map(int, current_version.split('.'))  
        new_version = f"{major}.{minor + 1}"  

        updated_section = (  
            f"{{{{version:{new_version}/{section_id}}}}}\n"  
            f"{args['new_content']}\n"  
            f"{{{{/version}}}}"  
        )  

        return re.sub(pattern, updated_section, current_story, 1, re.DOTALL)  

# Sample Usage  
if __name__ == "__main__":  
    diff_tool = StoryDiffTool()  

    # Read initial template  
    with open("story_flat.md") as f:  
        story = f.read()  

    # Apply sample edits  
    story = diff_tool.run(story, {  
        "section_id": "hook",  
        "new_content": "The peace treaty was signed 24 hours after the alien invasion began"  
    })  

    story = diff_tool.run(story, {  
        "section_id": "setting",  
        "new_content": "Floating cities anchored to radioactive storm clouds\nTime flows backward in contamination zones"  
    })  

    story = diff_tool.run(story, {  
        "section_id": "twist",  
        "new_content": "The human ambassador is revealed to be a parallel universe invader"  
    })  

    # Write output  
    with open("story_output.md", "w") as f:  
        f.write(story)  

    print("Story generation complete. Output saved to story_output.md")  

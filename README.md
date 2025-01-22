# AI Agent Examples
A collection of experimental implementations exploring different AI agent patterns and interactions.

## Storytelling Roundtable
An experiment in multi-agent story generation using versioned content modifications.

### Concept
Multiple AI agents collaborate to improve a story through sequential modifications. Each agent specializes in a specific narrative element (world-building, character development, plot twists) and can modify story sections using a versioned diff system.

### Implementation

#### storygen.py
Core implementation of the diff tool that enables versioned story modifications:
```python
from storytelling_roundtable.storygen import StoryDiffTool

diff_tool = StoryDiffTool()
story = diff_tool.run(story, {
    "section_id": "hook",
    "new_content": "The peace treaty was signed 24 hours after the invasion began"
})
```

#### story_flat.md
Template file defining story sections with version tracking:
```markdown
{{version:1.0/hook}}
## Opening Hook
[Create immediate intrigue/action]
{{/version}}

{{version:1.0/setting}}
## Core Setting
[Environment/time period/unique physical laws]
{{/version}}

{{version:1.0/characters}}
## Central Characters
- [Protagonist]: [Key motivation]
- [Opposition]: [Nature of conflict source]
{{/version}}

{{version:1.0/incident}}
## Inciting Incident
[Event that disrupts status quo]
{{/version}}

{{version:1.0/progression}}
## Action Progression
[Key story beats]
{{/version}}

{{version:1.0/twist}}
## Revelation/Twist
[Unexpected truth that reframes conflict]
{{/version}}

{{version:1.0/resolution}}
## Resolution Path
[Concrete steps toward climax]
{{/version}}

{{version:1.0/close}}
## Final Impact
[Lasting impression/visual/metaphor]
{{/version}}
```

### Quick Start
```bash
# Clone repository
git clone https://github.com/yourusername/ai_agent_examples.git
cd ai_agent_examples

# Run example
cd storytelling_roundtable
python storygen.py

# Check output
cat story_output.md
```

### How It Works
1. Story sections are wrapped in version tags
2. Each agent can modify sections using the diff tool
3. Versions increment automatically (1.0 → 1.1)
4. Changes maintain history through version tags

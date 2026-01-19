# Advanced Workflows

Power user strategies for maximizing productivity with Thesis.

## Multi-Document RAG Strategies

### Optimizing Document Context

Thesis searches your documents to provide contextual responses. Maximize effectiveness:

**Curate for quality:**
- Upload high-quality, well-structured documents
- Remove outdated versions that conflict with current practices
- Keep document titles descriptive and accurate

**Organize for retrieval:**
- Use clear section headers in your documents
- Break large documents into logical smaller files
- Ensure key terms and concepts appear in context

**Strategic uploading:**
- Upload your most-referenced materials first
- Add client-specific docs before starting client work
- Include both foundational materials and specific examples

### Scoping Document Search

For specific projects, focus Thesis's search:

```
"Using only the Acme Corp documents, create a training outline"
"Reference our company values document for this culture training"
"Based on the competency framework I uploaded, design this assessment"
```

This prevents mixing unrelated content from different clients or projects.

### Building a Knowledge Library

Create a comprehensive reference library:

1. **Foundation layer** - Core L&D frameworks and methodologies
2. **Organization layer** - Company standards, templates, style guides
3. **Client layer** - Client-specific materials for active projects
4. **Project layer** - Research and resources for current work

Remove client and project documents when work completes to keep search relevant.

## Complex Project Setups

### Multi-Phase Projects

For large initiatives spanning weeks or months:

**Project structure:**
1. Create a dedicated project in Thesis
2. Use consistent conversation naming (e.g., "Acme - Needs Analysis", "Acme - Curriculum Design")
3. Document key decisions in conversation summaries
4. Export important outputs for external storage

**Phase transitions:**
```
"We completed the analysis phase. Summarize key findings before we move
to design. Include the agreed learning objectives and constraints."
```

**Continuity across sessions:**
```
"In our previous conversation, we designed modules 1-3. Let's continue
with module 4, maintaining the same format and approach."
```

### Team Collaboration Patterns

When multiple L&D professionals work on the same project:

**Divide and conquer:**
- Assign different modules to different team members
- Each person works in their own conversations
- Use consistent templates for outputs

**Shared standards:**
- Upload shared style guides and templates
- Reference organization-wide documents
- Use the same project naming conventions

**Knowledge transfer:**
- Export key conversations for teammates
- Summarize decisions in shared documentation
- Use project descriptions for context

## Conversation Organization at Scale

### Managing Many Conversations

As your conversation history grows:

**Naming strategy:**
```
[Client/Project] - [Topic] - [Date or Version]
Examples:
- Acme Corp - Sales Curriculum - v2
- Internal - Leadership 360 Assessment
- Client X - Compliance Analysis - Jan 2024
```

**Regular cleanup:**
- Archive completed project conversations monthly
- Delete test or draft conversations
- Consolidate related conversations when possible

**Use projects:**
- Assign every work conversation to a project
- Keep personal/test conversations in a "Sandbox" project
- Review project assignments quarterly

### Finding Past Work

**Search strategies:**
- Search for deliverable type: "facilitator guide", "assessment"
- Search for client or project names
- Search for unique methodology terms

**Reference in new conversations:**
```
"I previously created a sales training curriculum for Acme Corp.
Create a similar structure for this new client."
```

## Integration Automation

### Google Drive Workflow

Optimize your Google Drive integration:

**Folder structure:**
```
L&D Resources/
├── Active Clients/
│   ├── Client A/
│   └── Client B/
├── Templates/
├── Frameworks/
└── Research/
```

**Sync strategy:**
- Set "Active Clients" to daily sync
- Set "Templates" and "Frameworks" to weekly
- Sync "Research" manually when adding new materials

**Automatic updates:**
- Edit documents in Drive; Thesis picks up changes automatically
- Add new files to synced folders for automatic inclusion
- Remove files from synced folders to exclude them

### Notion Workflow

For Notion integration:

**Page organization:**
- Create a dedicated "Thesis Resources" workspace section
- Use consistent page naming
- Structure pages with clear headers for better chunking

**Database content:**
- Database entries become individual searchable documents
- Keep entries focused on single topics
- Use consistent property structures

## Performance Optimization

### Faster Responses

Get quicker results from Thesis:

**Focused requests:**
```
GOOD: "Create 5 multiple choice questions on customer de-escalation"
BAD: "Create an assessment" (too vague)
```

**Incremental development:**
```
GOOD: "First, outline module 1. Then we'll add details."
BAD: "Create a complete 40-hour curriculum with all activities and materials"
```

**Limit scope per message:**
```
GOOD: "Expand section 3 with learning activities"
BAD: "Expand all sections and add activities and create assessments for each"
```

### Reducing Iterations

Minimize back-and-forth corrections:

**Provide complete context upfront:**
```
"Create a facilitator guide for a 90-minute workshop on giving feedback.
Audience: First-time managers at a tech company.
Format: Mix of discussion and role-play.
Include: Time allocations, discussion questions, role-play scenarios.
Avoid: Lecture-heavy content or reading exercises."
```

**Reference existing work:**
```
"Use the same format as the customer service guide we created last week"
"Apply our company's 4-step feedback model"
```

**Specify quality expectations:**
```
"Create a polished, client-ready version"
"Give me a rough draft to start"
```

## Advanced Prompt Techniques

### Structured Prompts

Use consistent structures for reliable outputs:

```
DELIVERABLE: [What you want]
AUDIENCE: [Who it's for]
CONTEXT: [Background/constraints]
FORMAT: [Structure/length requirements]
INCLUDE: [Required elements]
AVOID: [What not to include]
```

### Chain of Thought Requests

For complex deliverables, build step by step:

```
1. "First, identify the key competencies for this role"
2. "Now, create learning objectives for each competency"
3. "Design activities that develop these competencies"
4. "Build assessment criteria for each competency"
5. "Create the facilitator guide bringing it all together"
```

### Meta-Prompts

Ask Thesis for help with prompting:

```
"What information do you need from me to create an effective assessment?"
"What format options would work best for this facilitator guide?"
"Help me structure my request for a comprehensive curriculum"
```

## Workflow Templates

### Complete Course Development

1. **Discovery:** "Help me understand the training need for [topic]" (Coach mode)
2. **Analysis:** "Analyze these requirements and identify learning gaps" (Analyst mode)
3. **Design:** "Create a curriculum outline based on our analysis" (Developer mode)
4. **Development:** "Develop module 1 with all activities and materials" (Developer mode)
5. **Assessment:** "/assess [module topic]" (Developer mode)
6. **Visuals:** "/image [scenario for training]" (Developer mode)
7. **Facilitation:** "Create a facilitator guide for module 1" (Developer mode)
8. **Review:** "Evaluate this curriculum against learning science principles" (Analyst mode)
9. **Strategy:** "How should I present this to stakeholders?" (Advisor mode)

### Rapid Deliverable

1. "/outline [topic]" - Get structure
2. "Expand module 2" - Add detail where needed
3. "/assess [topic]" - Add assessment
4. "Create one-page summary" - Executive version
5. Export all

### ROI-Focused Project

1. "/roi [initiative]" - Establish measurement framework
2. "What training would impact these metrics?" - Connect learning to business
3. "/outline [training approach]" - Design the intervention
4. "Create executive summary with ROI projections" - Stakeholder version

## Troubleshooting Advanced Issues

### Context Drift

**Problem:** Long conversations lose focus.

**Solutions:**
- Start new conversations for distinct phases
- Periodically summarize: "Summarize what we've agreed on so far"
- Reference earlier decisions explicitly

### Conflicting Document Information

**Problem:** Documents contain conflicting guidance.

**Solutions:**
- Remove outdated documents
- Be explicit: "Use the 2024 version of our framework"
- Consolidate documents with updates

### Output Quality Degradation

**Problem:** Outputs become less detailed over time.

**Solutions:**
- Start fresh conversations periodically
- Repeat key quality expectations
- Break large requests into smaller pieces

## Related Guides

- [Operating Modes](10-operating-modes.md) - Mode selection
- [Document Management](02-document-management-overview.md) - Document strategies
- [Project Management](05-project-management.md) - Organizing work
- [Templates and Shortcuts](08-templates-and-shortcuts.md) - Quick commands

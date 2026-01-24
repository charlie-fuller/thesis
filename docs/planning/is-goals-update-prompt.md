# Prompt: Update IS Goal Alignment Analyzer

Use this prompt when you have the full IS team FY27 strategic goals documentation.

---

## What I Need

Please update the Goal Alignment Analyzer (`/backend/services/goal_alignment_analyzer.py`) with our actual IS team strategic goals. Here's the information I'm providing:

**[PASTE YOUR GOALS DOCUMENT OR DETAILS HERE]**

---

## Information That Would Be Helpful

1. **Strategic Pillars** - The main goal areas/themes (currently assuming 4, but could be more or fewer)
   - Name of each pillar
   - Description of what success looks like
   - Key outcomes or deliverables

2. **KPIs & Targets** - Specific measurable targets for FY27
   - Current baseline numbers
   - Target numbers
   - How they're measured

3. **Weighting** (optional) - Are some pillars more important than others?
   - If so, what's the relative priority?

4. **Key Initiatives** - Specific projects or programs that define the strategy
   - Names and descriptions
   - Which pillar they support

5. **Context** - Any additional context that would help score opportunities
   - What does "Insight 360" mean?
   - What counts as a "production agent"?
   - Definition of "zero friction lifecycle"?

---

## What Will Be Updated

Once you provide this information, I'll update:

1. **`IS_GOALS` constant** in `goal_alignment_analyzer.py` - The pillar definitions, descriptions, and KPIs

2. **Scoring prompt** - The prompt sent to Claude to analyze opportunities will be updated with accurate goal descriptions

3. **Pillar weights** (if needed) - Currently each pillar is 25 points; can adjust if some are more important

4. **Frontend labels** in `GoalAlignmentSection.tsx` - The pillar names, descriptions, and KPI badges displayed in the UI

---

## Current Implementation (for reference)

The analyzer currently uses these 4 pillars (25 pts each = 100 total):

```python
IS_GOALS = {
    "decision_ready_journey": {
        "name": "Decision-Ready Customer Journey",
        "description": "Connected systems provide full visibility to make faster, better decisions",
        "kpis": ["Zero Friction Lifecycle Issues (15/mo -> 0/mo)"]
    },
    "maximize_systems_ai": {
        "name": "Maximize Business Systems & AI Value",
        "description": "Right-size the portfolio, support AI initiatives, and maximize ROI",
        "kpis": ["Production Agents (15 -> 50+)"]
    },
    "data_first_workforce": {
        "name": "Data-First Digital Workforce",
        "description": "Insight 360 enables agentic capabilities to solve business problems",
        "kpis": ["AI Agent Success Rate (4% -> 80%)", "Self-Service Analytics (45% -> 80%)"]
    },
    "high_trust_culture": {
        "name": "High-Trust IS Culture",
        "description": "Team development and stakeholder communication build trust",
        "kpis": ["Team Development Score", "Stakeholder Satisfaction"]
    }
}
```

---

## Example Update Request

"Here are our actual IS goals from our FY27 strategy deck:

**Pillar 1: Customer Experience Excellence** (30% weight)
- Goal: Eliminate friction in customer lifecycle
- KPI: Customer effort score from 4.2 to 3.0
- KPI: Support ticket volume -40%
- Key initiative: Unified customer portal

**Pillar 2: AI-Powered Operations** (30% weight)
...

Please update the goal alignment analyzer with these."

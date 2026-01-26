# CinnaM0n Sentiment Analysis Framework

**Purpose:** Reference framework for emotional and relationship analysis during synthesis
**Used By:** Synthesizer Agent (Step 2.25)
**Origin:** Adapted from CinnaM0n v1.0 sentiment analysis system

---

## Why Sentiment Analysis Matters

Stakeholders don't always say what they mean. Emotional signals reveal:
- **True priorities** - High frustration = high pain, regardless of stated priority
- **Hidden resistance** - Skepticism that won't surface in rational discussion
- **Adoption risks** - Who will champion vs. who will block
- **Relationship dynamics** - Alliances and tensions that affect decision-making

A technically perfect solution that ignores emotional reality will fail.

---

## Critical: Sentiment Has a TARGET

**Sentiment is not just positive/negative - it's an emotion ABOUT something.**

The same emotion means very different things depending on what it's directed at:

| Emotion | Target | Interpretation | Implication |
|---------|--------|----------------|-------------|
| Frustration | Current process | **GOOD** - Pain point validated, want change | Strong motivation for solution |
| Frustration | Our discovery approach | **BAD** - Losing them, process friction | Adjust approach, address concern |
| Frustration | A specific tool/system | **NEUTRAL** - May or may not be in scope | Clarify if this is something we're solving |
| Frustration | Another team/person | **CAUTION** - Political landmine | Don't amplify; note for relationship dynamics |
| Skepticism | Proposed solution | **USEFUL** - Need to prove value | Plan for pilot/proof-of-concept |
| Skepticism | AI/automation in general | **RISK** - Deep resistance | Change management critical |
| Skepticism | Previous failed attempts | **CONTEXT** - Burned before | Address history explicitly |
| Enthusiasm | Initiative/solution | **CHAMPION** - Ally for adoption | Engage early, leverage influence |
| Enthusiasm | Their own role in it | **MIXED** - May be self-serving | Verify alignment with broader goals |
| Enthusiasm | Technology for its own sake | **CAUTION** - May not translate to adoption | Ground in business outcomes |

### How to Capture Sentiment Targets

When noting emotional markers, always include the object:

**Format:** `[Emotion] ABOUT [Target] - "[Evidence]" - [Speaker]`

**Examples:**
- `Frustration ABOUT data fragmentation - "70-80 places, maybe even more" - Steve`
- `Skepticism ABOUT AI reliability - "you have to know enough to know what sounds generic" - Matt`
- `Enthusiasm ABOUT quick wins - "10% that we can absolutely crush" - Tyler`
- `Resignation ABOUT process consistency - "that's just how it is" - Thomas`

### Sentiment Target Categories

Track sentiment across these target categories:

| Target Category | What It Tells You |
|-----------------|-------------------|
| **Current state/process** | Pain point severity, change motivation |
| **Proposed solution** | Buy-in level, adoption likelihood |
| **Specific tools/systems** | Technical constraints, preferences |
| **Other teams/people** | Political landscape, collaboration risks |
| **Our discovery process** | Whether we're on track or need to adjust |
| **Timeline/urgency** | Real vs. manufactured pressure |
| **Their own role** | Self-interest alignment with initiative |
| **Leadership/sponsors** | Trust in decision-makers, likelihood of support |

### Output: Enhanced Sentiment Table

Include sentiment targets in the Stakeholder Sentiment Summary:

```markdown
### Stakeholder Sentiment Summary

| Stakeholder | Emotion | Target | Intensity | Implication |
|-------------|---------|--------|-----------|-------------|
| Tyler | Enthusiasm | Quick win approach | 8/10 | Champion for phased delivery |
| Thomas | Skepticism | Prompt standardization | 6/10 | Wants sophistication, not templates |
| Matt L | Frustration | Data verification time | 9/10 | High-priority pain point |
| Farsheed | Reserved | Unknown | ? | Silent - need follow-up |

> **Key Insight:** Frustration is directed at current process (good - validates pain), not at our approach. Skepticism is about specific solutions, not the initiative itself - addressable with proof-of-concept.
```

---

## Output Templates for Synthesis

The Synthesizer includes sentiment insights in its outputs. Use these templates:

### Stakeholder Sentiment Summary (in Synthesis Summary)

```markdown
### Stakeholder Sentiment Summary

| Stakeholder | Role | Primary Emotion | Intensity | Change Readiness | Champion Potential |
|-------------|------|-----------------|-----------|------------------|-------------------|
| [Name] | [Role] | [Emotion] | [1-10] | [H/M/L] | [H/M/L] |

> **Sentiment Insight:** [Key observation about emotional landscape and adoption implications]
```

### Detailed Stakeholder Analysis (when needed)

For complex initiatives with high stakeholder tension, include:

```markdown
#### [Stakeholder Name] - [Role]

**Primary Emotion:** [Emotion] - Intensity: [1-10]
**Evidence:** "[Verbatim quote showing emotion]"

**Change Readiness:** [High / Medium / Low / Unknown]
**Rationale:** [Why this assessment]

**Red Flags:** [Any concerning signals]
**Champion Potential:** [High / Medium / Low]
```

---

## Relationship Dynamics

### Alliances (Aligned Perspectives)
| Stakeholder A | Stakeholder B | Evidence | Implication |
|---------------|---------------|----------|-------------|
| [Name] | [Name] | "[Quote or behavior]" | [What this means for initiative] |

### Tensions (Conflicting Perspectives)
| Stakeholder A | Stakeholder B | Tension Point | Evidence | Resolution Needed |
|---------------|---------------|---------------|----------|-------------------|
| [Name] | [Name] | [Topic] | "[Quote]" | [Who should mediate] |

### Power Dynamics
- **Most influential voice:** [Name] - [Evidence]
- **Deferred to by others:** [Name] - [Who defers and when]
- **Voices that got cut off or ignored:** [Name] - [What happened]

---

## Pain Point Emotional Weighting

| Pain Point | Stated Priority | Emotional Intensity | Adjusted Priority | Rationale |
|------------|-----------------|---------------------|-------------------|-----------|
| [Issue] | [L/M/H] | [1-10] | [L/M/H] | [Why adjustment] |

> **Insight:** Pain points with high emotional intensity but low stated priority may be normalized suffering - "that's just how it is" - and represent significant opportunity.

---

## Change Readiness Assessment

### Overall Readiness: [High / Medium / Low / Mixed]

**Enablers (Positive Signals):**
- [Signal]: "[Evidence]" - [What it enables]

**Barriers (Negative Signals):**
- [Signal]: "[Evidence]" - [Risk it creates]

**Unknown Factors:**
- [Stakeholder/Area] - [Why uncertain] - [How to probe]

---

## Adoption Risk Analysis

### High-Risk Stakeholders
| Stakeholder | Risk Type | Evidence | Mitigation |
|-------------|-----------|----------|------------|
| [Name] | [Skepticism/Defensiveness/etc.] | "[Quote]" | [Suggested approach] |

### Champions to Leverage
| Stakeholder | Why Champion | How to Engage |
|-------------|--------------|---------------|
| [Name] | [Evidence of enthusiasm] | [Specific action] |

---

## Silent Stakeholder Analysis

| Stakeholder | Speaking Time | Topics Silent On | Possible Reasons | Recommendation |
|-------------|---------------|------------------|------------------|----------------|
| [Name] | [~X%] | [Topics] | [Interpretation] | [Follow-up action] |

**Silence Interpretation Guide:**
- Agreement: Nodding, brief affirmations, no objections
- Disengagement: Looking away, side conversations, checking phone
- Suppressed disagreement: Facial expressions, abrupt topic changes, "yeah but..."
- Outside expertise: Deference on technical topics

---

## Urgency Assessment

### Genuine Urgency Signals
| Signal | Evidence | Business Impact |
|--------|----------|-----------------|
| [Signal] | "[Quote]" | [Real deadline or consequence] |

### Manufactured/Emotional Urgency
| Signal | Evidence | Reality Check |
|--------|----------|---------------|
| [Signal] | "[Quote]" | [Why this may be inflated] |

---

## Key Quotes by Emotion

### Frustration
- "[Quote]" - [Speaker] - [What it reveals]

### Enthusiasm
- "[Quote]" - [Speaker] - [What it reveals]

### Skepticism
- "[Quote]" - [Speaker] - [What it reveals]

### Resignation
- "[Quote]" - [Speaker] - [What it reveals]

---

## Recommendations for Synthesis

Based on sentiment analysis:

1. **Prioritize differently:** [Specific pain points that deserve higher priority based on emotional weight]

2. **Address resistance:** [Specific stakeholders/concerns that need mitigation in approach]

3. **Leverage champions:** [Who to engage first and how]

4. **Follow up with:** [Silent/underrepresented stakeholders who need dedicated sessions]

5. **Watch for:** [Relationship dynamics that could derail implementation]

---

*Generated using CinnaM0n Sentiment Analysis Agent v1.0*
```

---

## Analysis Framework

### 1. Emotional Pattern Recognition

**Signal Words and Phrases:**

| Emotion | Verbal Signals | Non-Verbal Signals (if noted) |
|---------|----------------|-------------------------------|
| **Frustration** | "always", "never", "every time", "waste", sighs | Interrupting, raising voice |
| **Enthusiasm** | "love", "excited", "can't wait", "finally" | Leaning in, fast speech |
| **Skepticism** | "we tried", "not sure", "maybe", "I guess" | Hesitation, trailing off |
| **Urgency** | "immediately", "critical", "deadline", "now" | Rapid speech, emphatic |
| **Resignation** | "that's just how", "nothing we can", "always been" | Flat tone, shrugging |
| **Defensiveness** | "but actually", "well, the thing is", "it's not my" | Crossed arms, justifying |
| **Anxiety** | "worried", "concerned", "what if", "risk" | Fidgeting, qualifying |

### 2. Relationship Dynamic Detection

**What to Look For:**

| Dynamic | Signals |
|---------|---------|
| **Alliance** | Building on each other's points, "like [Name] said", nodding |
| **Tension** | Interrupting, "but actually", ignoring points, side-glances |
| **Deference** | "What do you think, [Name]?", waiting for senior to speak first |
| **Dominance** | Speaking longest, interrupting others, setting agenda |
| **Exclusion** | Not being addressed, ideas not acknowledged, talked over |

### 3. Change Readiness Indicators

| Readiness Level | Signals |
|-----------------|---------|
| **High** | "Finally", proactive suggestions, volunteering for pilots |
| **Medium** | Open questions, conditional support ("if it works...") |
| **Low** | "We tried that", "won't work here", focus on obstacles |
| **Resistant** | Dismissive, changing subject, defending status quo |

---

## How to Apply (During Synthesizer Step 2.25)

While processing transcripts, apply these analysis passes:

### Pass 1: Map Speaking Patterns
For each participant:
- Estimate speaking share (%)
- Note when they speak (start, middle, end of discussions)
- Note what topics trigger their engagement

### Pass 2: Identify Emotional Markers
Scan for signal words and phrases from the framework above.
Tag each with:
- Speaker
- Emotion
- Intensity (1-10)
- Context

### Pass 3: Analyze Relationships
Look for interaction patterns:
- Who responds to whom
- Who gets interrupted
- Who gets deferred to
- Who gets ignored

### Pass 4: Assess Change Readiness
For each stakeholder:
- What signals indicate openness to change?
- What signals indicate resistance?
- What's unknown?

### Pass 5: Re-Weight Pain Points
Compare stated priorities vs. emotional intensity:
- High emotion + Low stated priority = **Normalized pain** (raise priority - opportunity!)
- Low emotion + High stated priority = **Mandated priority** (may lack buy-in)
- High emotion + High stated priority = **Genuine urgent pain**

---

## Quality Checklist (for Synthesizer)

When sentiment analysis is applied correctly:
- [ ] Every stakeholder with >10% speaking time has emotion noted
- [ ] Primary emotion identified with quote evidence for each
- [ ] Change readiness assessed for key stakeholders
- [ ] Relationship dynamics mapped (alliances, tensions)
- [ ] Silent stakeholders acknowledged with interpretation
- [ ] Pain points re-weighted based on emotional intensity
- [ ] Stakeholder Sentiment Summary included in Synthesis output

---

## Integration with Synthesizer

This framework is applied during **Step 2.25** of the Synthesizer workflow. The Synthesizer reads transcripts through both a content lens (what was said) and an emotional lens (how it was said).

**How Synthesizer Uses This Framework:**
1. Apply emotional pattern recognition while extracting findings (Step 2)
2. Map relationship dynamics between stakeholders
3. Assess change readiness for each stakeholder
4. Re-weight pain point priorities based on emotional intensity
5. Include Stakeholder Sentiment Summary in outputs
6. Surface adoption risks in Gap Report

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-01-22 | Initial CinnaM0n framework integrated into Synthesizer |

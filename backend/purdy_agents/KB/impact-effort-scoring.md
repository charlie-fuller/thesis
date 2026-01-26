# Impact-Effort Scoring Framework

## Purpose
Provide consistent criteria for evaluating and prioritizing opportunities identified during discovery. This framework enables objective comparison across different types of initiatives.

---

## Impact Scoring (1-5)

### Business Impact Dimensions

| Dimension | Description |
|-----------|-------------|
| **Revenue** | Direct impact on revenue growth, retention, or expansion |
| **Efficiency** | Time/cost savings, productivity gains |
| **Risk Reduction** | Mitigation of business, compliance, or operational risks |
| **Strategic Alignment** | Enablement of broader strategic goals |
| **User Experience** | Improvement in satisfaction, adoption, or capability |

### Impact Score Definitions

| Score | Label | Description |
|-------|-------|-------------|
| **5** | Transformative | Fundamental change to how we operate; major strategic enabler; significant revenue impact (>$1M/year) |
| **4** | High | Clear, substantial improvement; meaningful revenue/efficiency gains ($250K-$1M/year equivalent) |
| **3** | Moderate | Noticeable improvement; solid value but not game-changing ($50K-$250K/year equivalent) |
| **2** | Low | Minor improvement; nice-to-have; limited measurable impact (<$50K/year equivalent) |
| **1** | Minimal | Negligible impact; primarily cosmetic or marginal improvement |

### Impact Assessment Questions

1. **How many people/processes are affected?**
   - 5: Company-wide or customer-wide
   - 4: Multiple departments or large customer segment
   - 3: Single department or moderate user group
   - 2: Small team or limited use case
   - 1: Individual or edge case

2. **How often does this matter?**
   - 5: Daily/continuous
   - 4: Weekly
   - 3: Monthly
   - 2: Quarterly
   - 1: Rarely/annually

3. **What's the severity when it occurs?**
   - 5: Business-critical/blocking
   - 4: Significant disruption
   - 3: Notable inconvenience
   - 2: Minor friction
   - 1: Trivial annoyance

---

## Effort Scoring (1-5)

### Effort Dimensions

| Dimension | Description |
|-----------|-------------|
| **Technical Complexity** | Engineering difficulty, unknowns, integrations |
| **Duration** | Calendar time to deliver |
| **Resources** | People, skills, and budget required |
| **Dependencies** | External factors, prerequisite work |
| **Change Management** | Training, adoption, process changes needed |

### Effort Score Definitions

| Score | Label | Description |
|-------|-------|-------------|
| **5** | Major | Large team, 6+ months, significant complexity/risk, major dependencies |
| **4** | Significant | Cross-functional team, 3-6 months, notable complexity |
| **3** | Moderate | Small team, 1-3 months, manageable complexity |
| **2** | Light | 1-2 people, 2-4 weeks, straightforward |
| **1** | Minimal | Single person, days to 1 week, simple/known solution |

### Effort Assessment Questions

1. **Technical complexity?**
   - 5: Requires new architecture, significant R&D, or unknown technology
   - 4: Complex integrations, multiple systems affected
   - 3: Moderate complexity, some integrations
   - 2: Straightforward, mostly configuration
   - 1: Simple, well-understood solution exists

2. **What skills are needed?**
   - 5: Rare expertise, external hires likely needed
   - 4: Specialized skills, internal experts scarce
   - 3: Available skills but capacity constrained
   - 2: Common skills, capacity available
   - 1: Any team member could do this

3. **What dependencies exist?**
   - 5: Multiple external/uncontrolled dependencies
   - 4: Key dependency on another team/initiative
   - 3: Some coordination needed
   - 2: Minor dependencies, easily managed
   - 1: Self-contained, no blockers

---

## Priority Matrix

```
           │  Low Effort (1-2)  │  Med Effort (3)   │  High Effort (4-5)
───────────┼────────────────────┼───────────────────┼────────────────────
High       │   🏆 QUICK WINS    │  ⭐ STRATEGIC     │  🎯 MAJOR BET
Impact     │   Do immediately   │  Plan & prioritize│  Evaluate carefully
(4-5)      │                    │                   │
───────────┼────────────────────┼───────────────────┼────────────────────
Medium     │   ✅ FILL-INS      │  📋 BACKLOG       │  ⚠️ RECONSIDER
Impact     │   Good for slack   │  Standard queue   │  May not be worth it
(3)        │   time             │                   │
───────────┼────────────────────┼───────────────────┼────────────────────
Low        │   🔄 OPPORTUNISTIC │  ❌ DEPRIORITIZE  │  🚫 AVOID
Impact     │   If truly easy    │  Not worth focus  │  Don't pursue
(1-2)      │                    │                   │
```

---

## Scoring Process

### Step 1: Individual Scoring
Each opportunity is scored independently:
- Assign Impact score (1-5) with rationale
- Assign Effort score (1-5) with rationale
- Calculate Priority Index = Impact × (6 - Effort)

### Step 2: Calibration
Compare scores across opportunities:
- Are relative rankings sensible?
- Are any scores outliers that need revisiting?
- Apply adjustments for strategic priority

### Step 3: Adjustment Factors

| Factor | Adjustment |
|--------|------------|
| **ELT Priority** | +1 Impact if explicitly called out as priority |
| **Dependencies Enable Other Work** | +1 Impact if this unblocks other high-value items |
| **Time Sensitivity** | +1 Impact if window of opportunity is closing |
| **Technical Debt** | -1 Effort if it reduces future complexity |
| **Learning Value** | +0.5 Impact if builds strategic capability |

---

## Example Scoring

### Opportunity: Automate Account Health Scoring

**Impact Assessment:**
- Affects: All account managers (~50 people) = 4
- Frequency: Weekly account reviews = 4
- Severity: Currently time-consuming, error-prone = 3
- Strategic: Enables proactive account management = 4
- **Impact Score: 4** (High - clear efficiency + strategic value)

**Effort Assessment:**
- Technical: Requires data integration, ML model = 4
- Skills: Data engineering + ML expertise needed = 4
- Dependencies: Requires clean data from CRM = 3
- Duration: Estimate 3-4 months = 4
- **Effort Score: 4** (Significant)

**Priority Index:** 4 × (6-4) = 8
**Category:** Major Bet - worth pursuing if resources available

---

## Output Format

When scoring opportunities, document as:

```markdown
## [Opportunity Name]

**Impact: [Score]** - [Label]
- [Rationale bullet 1]
- [Rationale bullet 2]

**Effort: [Score]** - [Label]
- [Rationale bullet 1]
- [Rationale bullet 2]

**Priority Index:** [Score]
**Category:** [Quick Win / Strategic / Major Bet / etc.]
**Recommendation:** [Pursue / Evaluate / Defer / Don't pursue]
```

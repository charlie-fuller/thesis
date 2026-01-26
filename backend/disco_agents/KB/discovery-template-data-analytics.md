# Discovery Template: Data Integration & Analytics

**Version:** 1.0
**Last Updated:** 2026-01-23

Use this template for initiatives where the core pattern is: "We need better data/visibility/reporting" or "Systems don't talk to each other."

---

## Pre-Meeting Knowledge Framework

### 1. Participant Knowledge

| Participant | Role | Data Domain | Stance | Power |
|-------------|------|-------------|--------|-------|
| [Name] | [Role] | [What data they own/use] | [Champion/Neutral/Skeptic] | [H/M/L] |
| | | | | |
| | | | | |

**What we still need to discover about participants:**
- [ ] Who owns the source data today?
- [ ] Who defines the business rules for transformation?
- [ ] Who will actually USE the output?

### 2. Problem/Opportunity Context

| Aspect | What We Know | What to Discover |
|--------|--------------|------------------|
| Source systems | | |
| Current data quality | | |
| Who validates data today | | |
| What decisions this informs | | |
| Freshness requirements | | |
| Historical data needs | | |

### 3. Desired Outcomes

| Outcome | Priority | Definition of Done |
|---------|----------|-------------------|
| Data source inventory | H | All sources with owners identified |
| Data quality assessment | H | Known issues documented |
| Transformation rules | H | Business logic documented |
| Decision mapping | H | What decisions, who makes them, how often |
| Freshness requirements | M | Real-time vs batch clarity |

### 4. Strategic Context

| Aspect | Status |
|--------|--------|
| Named executive sponsor | [ ] |
| Strategic priority alignment | |
| Timeline/urgency | |
| Budget constraints | |
| Dependencies | |

---

## Hypotheses to Test

### H1: Problem Hypothesis
**We believe:** [The core data problem is...]
**Expected evidence:** [We expect to see...]
**If wrong, we'd see:** [We'd find instead...]

### H2: Solution Hypothesis
**We believe:** [The right data approach is...]
**Who agrees:** [Expected champions]
**Who disagrees:** [Expected resistors]

### H3: Adoption Hypothesis
**We believe people will use this because:** [Reason]
**Key enablers:**
**Key barriers:**

### H4: Hidden Issue Hypothesis
**We suspect:** [There's a data quality/ownership issue around...]
**Detection signal:** [Listen for...]

---

## Required Questions (MUST answer before synthesis)

### Data Ownership (CRITICAL)
- [ ] "Who owns this data today?"
- [ ] "Who decides what the 'right' value is when sources conflict?"
- [ ] "Who resolves data quality issues?"

### Data Quality
- [ ] "How accurate is the current data? What's your confidence level?"
- [ ] "What happens when bad data gets in?"
- [ ] "Who validates data before it's used for decisions?"

### Transformation Logic
- [ ] "What business rules determine how source data becomes target data?"
- [ ] "Who knows all the edge cases in the transformation?"
- [ ] "When the rules change, who updates them and how?"

### Sync Requirements
- [ ] "Does this need to be real-time or is batch acceptable?"
- [ ] "What's acceptable latency between source change and target update?"
- [ ] "How do you handle conflicts when sources disagree?"

### Decision Usage (CRITICAL for analytics)
- [ ] "What specific decisions will this data inform?"
- [ ] "Who makes those decisions? How often?"
- [ ] "What action happens AFTER someone sees this report?"

---

## Optional Questions (nice to have)

### History
- [ ] "How far back do we need historical data?"
- [ ] "At what granularity (daily, monthly, yearly)?"
- [ ] "Has this been attempted before? What happened?"

### Access & Security
- [ ] "Who can see what? Any sensitivity concerns?"
- [ ] "Are there compliance requirements for this data?"

### Trust Building
- [ ] "What would build your confidence in this data?"
- [ ] "How do you verify data is correct today?"

---

## Type-Specific Failure Patterns to Watch

| Pattern | Why Data Initiatives Fail Here | Detection Questions |
|---------|--------------------------------|---------------------|
| **Ownership vacuum** | No one is accountable for data quality | "When data is wrong, who fixes it?" |
| **Transformation complexity** | Edge cases multiply | "What percentage of records have exceptions?" |
| **Nobody uses it** | Report built but not decision-actionable | "What happens AFTER you see this report?" |
| **Freshness mismatch** | Real-time expected, batch delivered | "How current does this data need to be?" |
| **Single source of truth myth** | Everyone has their own version | "Do Finance and Sales use the same numbers?" |
| **Data quality denial** | "Our data is fine" (it's not) | "Show me a sample row - is this accurate?" |

---

## Type-Specific Success Benchmarks

| Metric | Poor | Average | Good | Our Target |
|--------|------|---------|------|------------|
| Data accuracy | <85% | 85-95% | >95% | |
| Decision confidence | Low | Medium | High | |
| Report usage rate | <20% | 20-50% | >70% | |
| Time to insight | Days | Hours | Minutes | |
| Source system coverage | <50% | 50-80% | >80% | |

---

## Quantification Gate Checklist

Before synthesis, we MUST have:

- [ ] Source systems: Complete inventory with owners
- [ ] Data quality: Current accuracy/completeness assessment
- [ ] Decision mapping: What decisions, who, how often
- [ ] Freshness: Required latency documented
- [ ] Volume: How much data, how often updated
- [ ] Current state cost: Time spent gathering/reconciling data manually

---

## Warning Signs (Red Flags from SAP Experience)

Watch for these signals that suggest deeper issues:

1. **"The data in [System] isn't reliable"** - Data quality is SOURCE problem, not integration
2. **"We need a single source of truth"** - Often means politics, not technology
3. **"Can AI clean up our data?"** - AI can't fix bad upstream processes
4. **"We already have this in [other system]"** - Fragmentation is often intentional
5. **"Leadership wants a dashboard"** - Ask: "What decision will they make differently?"

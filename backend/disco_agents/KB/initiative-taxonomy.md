# Initiative Taxonomy

**Purpose:** Auto-classify initiative type, apply type-specific frameworks and benchmarks
**Capability:** Moves from unique treatment to pattern leverage
**Usage:** Early classification enables targeted question banks, failure pattern awareness, and benchmarking

---

## Why Classification Matters

Different initiative types have predictable patterns:

| Initiative Type | Common Failure Mode | Key Questions Often Missed | Success Metrics |
|-----------------|---------------------|---------------------------|-----------------|
| Data Integration | Underestimating transformation complexity | Data ownership, quality rules, sync frequency | Data accuracy %, sync latency |
| Process Automation | Ignoring edge cases | Exception handling, manual override, audit trail | Automation rate, exception rate |
| Tool Selection | Feature fixation over workflow fit | Migration path, training, organizational readiness | Adoption rate, time to productivity |
| Cross-Functional | Assuming alignment exists | RACI clarity, incentive alignment, governance | Handoff efficiency, escalation rate |

---

## The Five Primary Types

### Type 1: Data Integration

**Definition:** Connecting, consolidating, or synchronizing data across systems

**Subtype Variants:**

| Subtype | Characteristics | Critical Considerations |
|---------|-----------------|------------------------|
| **System Consolidation** | Reducing N systems to fewer | Data migration, feature parity, cutover strategy |
| **Data Pipeline** | ETL/ELT between systems | Transformation rules, sync frequency, error handling |
| **Master Data Management** | Single source of truth | Governance, golden record rules, distribution |
| **Analytics/BI Foundation** | Data for reporting | Data modeling, refresh cadence, access control |

**Classification Signals:**
- "Data is in multiple places"
- "Systems don't talk to each other"
- "We need a single source of truth"
- "Reports take too long because of data gathering"

**Type-Specific Question Bank:**

| Category | Essential Questions |
|----------|-------------------|
| **Ownership** | Who owns the data today? Who decides data rules? Who resolves conflicts? |
| **Quality** | What's current data quality? Who validates? What happens to bad data? |
| **Transformation** | What logic maps source to target? Who knows the edge cases? |
| **Sync** | Real-time or batch? What's acceptable latency? How to handle conflicts? |
| **History** | What historical data? How far back? In what granularity? |

**Common Failure Patterns:**
1. **Transformation Underestimation:** "Just map field A to field B" (ignores conditional logic)
2. **Governance Vacuum:** No one owns cross-system data rules
3. **Quality Cascade:** Bad data in source poisons target
4. **Sync Wars:** Conflicting updates from multiple sources

**Success Benchmarks:**

| Metric | Poor | Average | Good | Excellent |
|--------|------|---------|------|-----------|
| Data accuracy | <90% | 90-95% | 95-99% | >99% |
| Sync latency | >1 day | Hours | Minutes | Real-time |
| Integration uptime | <99% | 99% | 99.5% | 99.9% |
| Time to new integration | >3 months | 1-3 months | 2-4 weeks | <2 weeks |

---

### Type 2: Process Automation

**Definition:** Automating manual tasks, workflows, or decision processes

**Subtype Variants:**

| Subtype | Characteristics | Critical Considerations |
|---------|-----------------|------------------------|
| **Task Automation** | Single repetitive tasks | Edge cases, error handling, monitoring |
| **Workflow Automation** | Multi-step processes | State management, parallel paths, escalation |
| **Decision Automation** | Rules-based decisions | Rule maintenance, override capability, audit |
| **RPA/Bot Automation** | UI-based automation | Brittleness, maintenance, alternative APIs |

**Classification Signals:**
- "We do this manually every day/week"
- "The process is well-defined but takes too long"
- "People make the same decisions repeatedly"
- "We need to scale without adding headcount"

**Type-Specific Question Bank:**

| Category | Essential Questions |
|----------|-------------------|
| **Happy Path** | What's the standard flow? What percentage follows happy path? |
| **Edge Cases** | What variations exist? Who handles exceptions today? |
| **Errors** | What can go wrong? How are errors handled? Who gets notified? |
| **Override** | When do humans need to intervene? How do they override? |
| **Audit** | What needs to be logged? Who reviews? Compliance requirements? |

**Common Failure Patterns:**
1. **Happy Path Bias:** Automation works 80% of time, exceptions overwhelm operations
2. **Invisible Override:** No way to manually correct when automation errs
3. **Audit Blindness:** Can't prove what happened or why
4. **Maintenance Orphan:** No one owns updating rules when business changes

**Success Benchmarks:**

| Metric | Poor | Average | Good | Excellent |
|--------|------|---------|------|-----------|
| Automation rate | <50% | 50-70% | 70-90% | >90% |
| Exception rate | >20% | 10-20% | 5-10% | <5% |
| False positive rate | >10% | 5-10% | 2-5% | <2% |
| Time to update rules | >1 month | 2-4 weeks | 1-2 weeks | <1 week |

---

### Type 3: Tool Selection/Implementation

**Definition:** Evaluating, selecting, and deploying new tools or platforms

**Subtype Variants:**

| Subtype | Characteristics | Critical Considerations |
|---------|-----------------|------------------------|
| **Replacement** | Swapping existing tool | Migration, retraining, feature parity |
| **Greenfield** | New capability, no incumbent | Workflow integration, adoption planning |
| **Consolidation** | Merging multiple tools | Feature union, user preference management |
| **Platform** | Foundation for multiple uses | Extensibility, governance, center of excellence |

**Classification Signals:**
- "We're evaluating vendors"
- "The current tool doesn't meet our needs"
- "We need to choose between X and Y"
- "We're implementing [new platform]"

**Type-Specific Question Bank:**

| Category | Essential Questions |
|----------|-------------------|
| **Fit** | What problems must it solve? What's nice-to-have vs. critical? |
| **Workflow** | How does this fit daily work? What changes for users? |
| **Integration** | What must it connect to? API requirements? Data flow? |
| **Migration** | What data/config moves? Who does migration? Timeline? |
| **Change** | Who needs training? How much behavior change? Who champions? |

**Common Failure Patterns:**
1. **Feature Fixation:** Chose for features, failed on workflow fit
2. **Demo Delusion:** Looked great in demo, failed in reality
3. **Migration Minimization:** Underestimated data/config migration
4. **Adoption Assumption:** Built it, but they didn't come

**Success Benchmarks:**

| Metric | Poor | Average | Good | Excellent |
|--------|------|---------|------|-----------|
| User adoption (3 months) | <30% | 30-50% | 50-80% | >80% |
| Time to productivity | >6 months | 3-6 months | 1-3 months | <1 month |
| Feature utilization | <20% | 20-40% | 40-70% | >70% |
| User satisfaction | <3/5 | 3-3.5/5 | 3.5-4/5 | >4/5 |

---

### Type 4: Cross-Functional Initiative

**Definition:** Changes requiring coordination across multiple teams or departments

**Subtype Variants:**

| Subtype | Characteristics | Critical Considerations |
|---------|-----------------|------------------------|
| **Process Handoff** | Improving between-team transitions | RACI clarity, SLAs, escalation |
| **Shared Service** | Creating centralized capability | Governance, prioritization, service levels |
| **End-to-End Workflow** | Optimizing full process chain | Process ownership, metrics alignment |
| **Organizational Change** | Restructuring or new operating model | Change management, incentives, culture |

**Classification Signals:**
- "This involves multiple departments"
- "We need to improve handoffs between teams"
- "Everyone's involved but no one owns it"
- "The process crosses organizational boundaries"

**Type-Specific Question Bank:**

| Category | Essential Questions |
|----------|-------------------|
| **RACI** | Who's Responsible, Accountable, Consulted, Informed for each step? |
| **Incentives** | How are teams measured? Do incentives align with shared goal? |
| **Escalation** | What happens when teams disagree? Who breaks ties? |
| **Governance** | Who owns the end-to-end process? How are changes approved? |
| **Metrics** | What's shared success look like? How is credit/blame distributed? |

**Common Failure Patterns:**
1. **RACI Vacuum:** Everyone's responsible = no one's responsible
2. **Incentive Conflict:** Teams optimized for local metrics, not shared outcome
3. **Escalation Gridlock:** No mechanism to resolve cross-team disputes
4. **Ownership Orphan:** No one owns the space between teams

**Success Benchmarks:**

| Metric | Poor | Average | Good | Excellent |
|--------|------|---------|------|-----------|
| Handoff efficiency | >5 days avg | 2-5 days | 1-2 days | <1 day |
| Escalation rate | >30% | 15-30% | 5-15% | <5% |
| Cross-team satisfaction | <3/5 | 3-3.5/5 | 3.5-4/5 | >4/5 |
| Process cycle time | Benchmark +100% | +50-100% | +0-50% | At benchmark |

---

### Type 5: Reporting/Analytics

**Definition:** Creating or improving business intelligence, dashboards, or analytics capabilities

**Subtype Variants:**

| Subtype | Characteristics | Critical Considerations |
|---------|-----------------|------------------------|
| **Operational Reporting** | Day-to-day metrics | Freshness, reliability, actionability |
| **Executive Dashboard** | Strategic visibility | Right metrics, drill-down, confidence |
| **Self-Service Analytics** | User-driven exploration | Data access, governance, skill building |
| **Advanced Analytics** | ML/AI-driven insights | Model maintenance, interpretability, trust |

**Classification Signals:**
- "We need better visibility into..."
- "Leadership wants a dashboard for..."
- "We can't answer this question easily"
- "Reporting takes too long"

**Type-Specific Question Bank:**

| Category | Essential Questions |
|----------|-------------------|
| **Decisions** | What decisions will this inform? Who makes them? How often? |
| **Freshness** | How current must data be? Daily? Hourly? Real-time? |
| **Trust** | Where does data come from? Who validates? What builds confidence? |
| **Access** | Who can see what? Any sensitivity concerns? |
| **Action** | What happens after seeing the report? Who acts on insights? |

**Common Failure Patterns:**
1. **Metric Myopia:** Tracking what's easy, not what matters
2. **Dashboard Graveyard:** Built, launched, never used
3. **Trust Deficit:** Users don't believe the numbers
4. **Action Gap:** Insights generated but not acted upon

**Success Benchmarks:**

| Metric | Poor | Average | Good | Excellent |
|--------|------|---------|------|-----------|
| Dashboard usage (weekly) | <20% of target users | 20-40% | 40-70% | >70% |
| Data freshness gap | >1 day | Hours | Minutes | Real-time |
| Decision influence | Rarely cited | Sometimes cited | Usually cited | Always cited |
| Time to answer questions | >1 week | 1-3 days | Same day | Self-service |

---

## Classification Protocol

### Step 1: Listen for Type Signals

During discovery, flag phrases that indicate initiative type:

| Signal Phrase | Likely Type | Follow-Up Question |
|---------------|-------------|-------------------|
| "Systems don't talk" | Data Integration | What data needs to flow where? |
| "We do this manually" | Process Automation | What percentage is exception? |
| "We're evaluating tools" | Tool Selection | What problem does the tool solve? |
| "Multiple teams involved" | Cross-Functional | Who owns the end-to-end? |
| "We need visibility" | Reporting/Analytics | What decisions will this drive? |

### Step 2: Confirm Classification

After initial classification, confirm with stakeholders:

```markdown
**Classification Check:**
"Based on what we've heard, this appears to be primarily a [Type] initiative
with elements of [Secondary Type]. Does that match your understanding?"
```

### Step 3: Apply Type-Specific Framework

Once confirmed:
1. Pull relevant question bank
2. Check for common failure patterns
3. Apply success benchmarks
4. Note subtype considerations

### Step 4: Document in Synthesis

```markdown
## Initiative Classification

**Primary Type:** [Type] - [Subtype]
**Secondary Elements:** [Other type considerations]

**Type-Specific Risks:**
- [Failure pattern 1 relevant to this initiative]
- [Failure pattern 2 relevant to this initiative]

**Success Benchmark Targets:**
| Metric | Industry Benchmark | Our Target |
|--------|-------------------|------------|
| [Metric] | [Benchmark] | [Target] |
```

---

## Hybrid Initiatives

Many initiatives span multiple types. Handle as follows:

### Identify Primary/Secondary
```markdown
**Example:** "Implement new CRM with sales process automation"

Primary: Tool Selection (new CRM implementation)
Secondary: Process Automation (sales workflow automation)
```

### Apply Both Question Banks
Pull questions from both types, prioritizing primary type questions.

### Watch for Combined Failure Patterns
Hybrid initiatives often fail at the intersection:
- Tool Selection + Automation: Tool chosen for features, but can't support automation
- Data Integration + Cross-Functional: Integration works but teams don't use shared data
- Reporting + Tool Selection: Dashboard built in tool users don't access

---

## Gap Detection: Type Coverage

The Coverage Tracker should flag:

| Gap | Type Implication |
|-----|------------------|
| No data ownership discussion | Data Integration needs governance |
| No exception handling plan | Process Automation at risk |
| No adoption plan | Tool Selection likely to fail |
| No RACI defined | Cross-Functional doomed |
| No decision mapping | Reporting will become shelfware |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-23 | Initial initiative taxonomy for PuRDy v2.5 |

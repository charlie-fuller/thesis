# Synthesis Summary: Strategic Account Planning v2.1

## Executive Summary

Strategic Account Planning (SAP) emerged as an ELT-driven initiative to standardize and automate the account planning process for Contentful's top 100 customers. Discovery sessions revealed a fragmented landscape where AEs spend significant time gathering data from 70-80+ different places instead of being with clients. The core problem isn't lack of data—it exists across multiple systems—but rather the manual effort required to aggregate, verify, and synthesize it into actionable intelligence.

The workshops identified a clear "gold standard" for what good account plans look like (Nationwide Whitespace Doc, Amazon Partner Leverage tab, Signet Exec Brief) and documented the end-to-end process from landscape definition through strategic alignment. Technical blueprinting was explicitly scoped out as an opportunity-stage activity. Key automation opportunities exist at the landscape/whitespace mapping stage (where Deep Research shows ~99% accuracy) and in internal footprint aggregation (where Glean agents are already providing value).

The primary tension is between the desire for comprehensive, standardized outputs and the practical reality that different accounts have different data availability, and AEs need flexibility to apply judgment. The team advocates a phased "10% at a time" approach rather than attempting a monolithic "one button" solution.

## Key Themes

### Theme 1: Data Fragmentation is the Core Problem
**Finding:** Account planning data exists but is scattered across 70-80+ sources with no unified view.
**Evidence:**
- "How do we collectively gather all the information needed on account when it's across, let's just say I can be randomly 70, 80 places, maybe even more." - Steve Letourneau
- Data sources identified: Salesforce, Tableau, BuiltWith, Wappalyzer, ZoomInfo, Crossbeam, Glean, ChatGPT, LinkedIn Sales Navigator, Gatekeeper, Granulate
**Implications:** The solution is aggregation and integration, not data creation. Quick wins come from surfacing existing data better.

### Theme 2: "Trust but Verify" is Universal
**Finding:** AI tools can do heavy lifting, but output requires verification—especially for customer-facing use.
**Evidence:**
- "I was still QA and QCing it using the many hundreds of citations it gives me" - Chris Powers on Deep Research
- "The thing goes like you have to know enough to know what sounds generic and what's potentially inaccurate. Otherwise you'll skip right past it." - Matt Lazar
- "There's a certain component where you need to build it, you have to insert it. AI can help certain things, but I think that it would be a danger if you just click a button." - Thomas
**Implications:** Automation should include validation steps; training on verification is critical; confidence scores should be visible.

### Theme 3: Standardization Without Rigidity
**Finding:** Team wants standard templates but needs flexibility for account-specific situations.
**Evidence:**
- "I think it should be organic, and then the AE should be accountable." - Thomas on AE/BDR split
- "It's not necessarily that we need a format. As long as it makes my life easier and works for what we're trying to accomplish, I'm open to whatever." - Matt Vosberg
- Different data availability for net new vs. existing customers acknowledged by multiple participants
**Implications:** Design for configurability; provide templates but don't enforce rigid workflows.

### Theme 4: Quick Wins Over Big Bang
**Finding:** Phased delivery of 10% improvements beats waiting for comprehensive solution.
**Evidence:**
- "Rather than talking about the 70 to 80% by a button, we talk about the 10% that we can absolutely crush and do that five times." - Tyler
- "Assume you do a deep research promptly give you the 99% that you're looking for. And you have a future state of Q and A with something that Charlie has built..." - Tyler describing chunked approach
**Implications:** Identify discrete, high-value automation targets; deliver incrementally; connect pieces over time.

## Stakeholder Perspectives

### Account Executives (Matt Lazar, Matt Vosberg, Chris Powers, Thomas)
- **Primary concerns:** Time spent on manual data gathering vs. client-facing time
- **Key needs:** Consolidated, accurate data in one place; gold standard templates; flexibility in approach
- **Success criteria:** "Less time on data gathering, more time on strategy and action"
- **Quote:** "At the end of the day, once you get into a bunch of subsidiaries, like LinkedIn is not going to facilitate that because you just have to go and do a different company." - Chris Powers on power mapping complexity

### BDRs (Joel, Meron)
- **Primary concerns:** Clear division of responsibility with AEs; ability to contribute at AE level
- **Key needs:** Standard processes to follow; defined scope of work
- **Success criteria:** "AE above line, BDR below line & wide"
- **Quote:** "Pretty much all BDRs should be able to execute the first step at the level of account executive." - Workshop discussion

### CSMs (Farsheed)
- **Primary concerns:** Being engaged proactively rather than chased for information
- **Key needs:** Clear questionnaire or process for contributing; visibility into what AEs need
- **Success criteria:** Structured handoff process
- **Note:** CSM involvement was highlighted as critical but currently informal

### Sales Leadership (Steve Letourneau, Rich)
- **Primary concerns:** Consistency across team; ELT visibility into accounts
- **Key needs:** Standardized output format; measurable improvement
- **Success criteria:** "70-80% of time in front of clients"
- **Quote:** "Currently, there's no consistency across our company. So there's no kind of set template, just a place to put them in Salesforce." - Rich

### IT/AI Team (Mikki, Tyler, Rob, Tom Woodhouse, Justin)
- **Primary concerns:** Building what actually helps vs. theoretical solutions
- **Key needs:** Clear requirements; domain expertise from sales team
- **Success criteria:** Adopted tools that save real time
- **Quote:** "Don't think about the tech. Think about how you would really like this to go, because that's what we want to hear." - Mikki

## Current State Summary

The current account planning process follows this general flow, with significant manual effort at each stage:

1. **Landscape Definition/Whitespace Mapping:** AE uses ChatGPT Deep Research with uploaded examples, validates output against BuiltWith/Wappalyzer, manually inspects sites for career pages/mobile/etc. BDR may assist with validation. Output goes into Excel or similar.

2. **Partner Leverage:** AE pulls subsidiary list into Salesforce, copies partner data from Crossbeam (via PM), reaches out to partner team for augmentation. Crossbeam data is often incomplete.

3. **Internal Footprint Audit:** AE reviews Salesforce for current product usage, space count, health metrics. Contacts CSM via Slack/email for context. Data is fragmented across multiple Tableau views. No standardized questionnaire.

4. **Power Mapping:** AE identifies C-Suite from LinkedIn Sales Navigator/ZoomInfo. Detailed relationship mapping happens at opportunity stage, not account planning. Outreach preferred over Excel for ongoing tracking.

5. **Strategic Alignment:** AE uses Deep Research (Gemini or ChatGPT) with curated prompt, may use Glean Account Navigator for existing customers. Output feeds IVP document via Value Engineering (Sean Winter).

6. **Technical Blueprinting:** OUT OF SCOPE - explicitly moved to opportunity stage by workshop consensus.

## Key Pain Points (Prioritized)

1. **Data Verification is Time-Consuming** - Severity: High
   - Impact: Every AE spends significant time validating AI outputs manually
   - Root cause: Standard ChatGPT unreliable; Deep Research better but still needs citation checking; ZoomInfo data often obsolete ("nine out of ten were obsolete")

2. **No Unified Product Usage View** - Severity: High
   - Impact: AEs must navigate multiple Tableau views to piece together account health
   - Root cause: "It seems to be split up into multiple views. Which some views have 80% information, and then you got to go to at least one or two other views." - Tom Woodhouse

3. **Crossbeam Access is Gated** - Severity: Medium
   - Impact: AEs cannot self-serve partner data; must go through Partner Managers
   - Root cause: AEs don't have direct access; data is incomplete anyway ("It's not necessarily good or bad crossbeam data. It's that not everybody has crossbeam." - Matt Vosberg)

4. **CSM Knowledge is Informal** - Severity: Medium
   - Impact: Critical internal footprint knowledge requires ad-hoc Slack/email conversations
   - Root cause: No standardized questionnaire or contribution process

5. **No Prompt/Process Library** - Severity: Medium
   - Impact: Each AE reinvents the wheel; good prompts not shared
   - Root cause: "We're definitely in the wild" on prompt standardization

## Tensions & Trade-offs

| Tension | Perspective A | Perspective B | Recommended Resolution |
|---------|---------------|---------------|------------------------|
| Automation vs. Human Judgment | AEs want data gathered automatically | Leadership wants consistency and visibility | Define clear boundary: AI gathers & aggregates, AE strategizes & validates |
| Comprehensive vs. Fast | Gold standard templates have many fields | Need to move quickly, not hours per account | Define minimum viable fields; progressive enhancement for strategic accounts |
| Net New vs. Existing Customers | Process should work for both | Available data is very different | Graceful degradation: same template, different fields populated based on what's available |
| Prompt Library vs. Natural Conversation | Some want standardized prompts | "Prompting is the past—it's about fluent conversation" - Thomas | Starter prompts for onboarding; advanced users can freestyle |

---

*Generated using PuRDy v2.1 Synthesizer with enhanced specificity requirements*

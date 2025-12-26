# Technical Writing Fundamentals for Software Engineers
## Clear Documentation, Better Products

### Program Snapshot
Enable software engineers to create clear, user-centered technical documentation that reduces support tickets and improves product adoption.

**Learners:** 80 software engineers (backend, frontend, DevOps)
**Duration:** 6-week self-paced + 4 live workshops
**Business Problem:** 40% of support tickets stem from unclear/missing documentation; costing $1.2M annually in support time

---

## The Business Case (DDLD)

### Data (Current State)
- **Support tickets related to documentation issues:** 40% of total (8,200/month)
- **Time spent per ticket:** 25 minutes average
- **Cost per ticket:** $15 (support engineer loaded rate)
- **Annual cost:** $1.23M (8,200 tickets/month × 12 months × $15)
- **Documentation coverage:** Only 60% of API endpoints have docs
- **Documentation accuracy:** 35% of existing docs are outdated
- **Developer time creating docs:** 2 hours/week (often copy-pasted without clarity review)

### Desired State
- **Support tickets from doc issues:** <15% (reduction of 25 percentage points)
- **Documentation coverage:** 95%+ of all public APIs and features
- **Documentation accuracy:** 90%+ (verified through quarterly audits)
- **Developer time creating docs:** 3 hours/week (more time, but higher quality = fewer iterations)
- **Cost savings:** $750K+ annually from reduced support tickets

### Learning Gap
Engineers can write code but struggle to:
1. Explain technical concepts to non-technical users
2. Structure documentation for different audience types (end users vs. developers)
3. Use plain language instead of jargon
4. Create effective code examples and tutorials
5. Maintain docs as code evolves

### Difference/Impact
Poor documentation → Users can't self-serve → Support tickets spike → Engineering time lost on preventable questions → Product adoption slows → Customer satisfaction drops.

---

## Behavior Changes We're Building

After this program, engineers will:

1. **Write user-first documentation** by asking:
   - Who is my reader? (persona)
   - What task are they trying to complete? (job-to-be-done)
   - What's the simplest path to success? (progressive disclosure)

2. **Apply the "Headings Test":** Could a reader scan just the headings and understand the doc structure? If not, revise.

3. **Use the "Code Example First" pattern:**
   - Show a working example upfront
   - Explain what it does (plain language)
   - Break down each component
   - Link to reference docs for deep dives

4. **Update docs as part of the development workflow:**
   - Include doc updates in every pull request
   - Use doc templates for consistency
   - Add "docs updated" as a PR checklist item

---

## Learning Outcomes

### Knowledge
- Explain the 4 types of technical documentation (Tutorial, How-To, Reference, Explanation)
- Identify 3 common reader personas for our product docs
- Describe the principles of plain language writing
- List the components of a complete API reference

### Skills
- Write clear, scannable headings that guide the reader
- Create code examples that demonstrate real-world use cases
- Revise jargon-heavy text into plain language
- Structure documentation using progressive disclosure (simple → complex)

### Performance (On-the-Job)
- 90% of engineers include doc updates in their pull requests
- Documentation coverage increases to 90%+ within 60 days
- Support tickets from doc issues decrease by 20% within 90 days
- Quarterly doc quality audits show 85%+ accuracy

---

## Program Structure

### Self-Paced Foundation (Weeks 1-6)
**Time commitment:** 1 hour/week

**Module 1: Why Documentation Matters (30 min)**
- The cost of bad docs (our data: $1.23M/year)
- User stories: Real support tickets caused by unclear docs
- Activity: Review 3 docs from our product - what's clear? What's confusing?

**Module 2: Know Your Reader (60 min)**
- The 3 reader personas for our docs:
  - End users (non-technical)
  - Integration engineers (technical, time-constrained)
  - Internal engineers (need deep technical details)
- Activity: Rewrite 1 doc paragraph for each persona

**Module 3: Structure for Scanning (60 min)**
- The "Headings Test" for scannable docs
- Progressive disclosure: Simple → Advanced
- Activity: Restructure a messy doc using headings and sections

**Module 4: Plain Language (60 min)**
- Replacing jargon with clear terms
- Active voice vs. passive voice
- Short sentences > long, complex sentences
- Activity: Plain language rewrite challenge (5 jargon-heavy paragraphs)

**Module 5: Code Examples That Teach (90 min)**
- The "Code Example First" pattern
- Anatomy of a great code example:
  - Minimal, runnable example
  - Clear comments explaining each step
  - Link to full reference docs
- Activity: Write a code example for 1 API endpoint

**Module 6: Docs-as-Code Workflow (45 min)**
- Treating docs like code (version control, reviews, CI/CD)
- Using templates for consistency
- PR checklist: "Docs updated" checkbox
- Activity: Update 1 doc and submit a pull request

---

### Live Workshops (4 × 90 minutes, bi-weekly)

**Workshop 1: Doc Critique & Peer Review (Week 2)**
- Small groups (8 engineers each)
- Each person brings 1 doc they've written
- Peer feedback using "Headings Test" and "Plain Language" rubric
- Revise in real-time based on feedback

**Workshop 2: Code Example Bootcamp (Week 4)**
- Live coding session: Write API examples together
- Review bad examples vs. good examples from real products
- Practice: Each engineer writes 2 code examples for our APIs
- Peer review and feedback

**Workshop 3: Advanced Topics (Week 6)**
- Diagrams for complex systems (when to use Mermaid, when to use screenshots)
- Video tutorials vs. written docs (when to use each)
- Internationalization considerations (writing for global audiences)
- Case studies: Great docs from other companies (Stripe, Twilio, Plaid)

**Workshop 4: Docs Showcase & Celebration (Week 8)**
- Each engineer presents 1 doc they've improved
- Voting: "Most Improved Doc" award
- Retrospective: What worked? What challenges remain?
- Roadmap: Next steps for sustaining doc quality

---

## Assessment Strategy

### Formative (During Learning)
- Self-assessments after each module (5 questions each)
- Peer reviews in Workshop 1 and 2
- Rubric scoring: Headings Test, Plain Language, Code Example Quality

### Summative (End of Program)
- **Final Project:** Write complete documentation for 1 new feature (or rewrite existing poor doc)
  - Must include: Tutorial, How-To, Reference, and Explanation sections
  - Scored by peer review (2 peers) + manager review
  - Passing score: 80%+

### Level 3 (Behavior Transfer - 30/60 days)
- Pull request audit: % of PRs that include doc updates
- Manager survey: "My engineers are updating docs consistently" (agree/disagree)
- Self-reported survey: Confidence in writing docs (1-5 scale)

### Level 4 (Business Impact - 90/180 days)
- Support ticket volume from doc issues (target: <15%)
- Documentation coverage (target: 90%+)
- Quarterly doc accuracy audit (target: 85%+)
- Cost savings from reduced support tickets (target: $750K+ annually)

---

## Success Metrics & ROI

### Investment
- Program design: $40,000
- Facilitation (4 workshops): $12,000
- Engineer time (6 weeks × 80 engineers × 2 hours/week × $85/hr): $81,600
- **Total: $133,600**

### Expected Return (12 months)
- Support ticket reduction (25% → 15% = 10 percentage points):
  - 8,200 tickets/month × 10% = 820 fewer tickets/month
  - 820 tickets × 12 months × $15/ticket = $147,600/year
- Improved product adoption (faster onboarding):
  - Estimated impact: 10% more users complete onboarding
  - 500 new users/month × 10% × $100 LTV = $60,000/year
- **Total return: $207,600**

**ROI: 55% over 12 months** (modest, but compounding - docs improve over time)

**Note:** ROI grows significantly in Year 2+ as doc quality continues improving without additional training investment.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Engineers don't prioritize docs in fast-paced sprints | Make "docs updated" a required PR checklist item; manager accountability |
| Existing docs too large to fix in 6 weeks | Start with highest-traffic docs (top 20% by views); iterate over time |
| Technical writers feel undermined | Partner with tech writing team to co-design program; they review final projects |
| Knowledge doesn't stick after program ends | Monthly "Doc of the Month" awards; quarterly refreshers |

---

## Sustainment (Post-Program)

**Months 1-3:**
- "Doc of the Month" awards (voted by team; $100 gift card)
- Monthly doc quality dashboard shared with leadership
- Slack bot reminders: "Don't forget docs in your PR!"

**Months 4-12:**
- Quarterly doc quality audits (L&D team + tech writers)
- New hire onboarding: All engineers complete Module 1-3 (90 min) in first week
- Advanced workshops (optional): API design docs, architectural decision records (ADRs)

**Year 2+:**
- Integrate doc quality into engineer performance reviews
- Expand program to Product Managers (writing user-facing release notes)

---

## Stakeholder Map

| Stakeholder | Role | Engagement |
|-------------|------|------------|
| 80 Software Engineers | Learners | Pre-program survey; feedback after each workshop |
| Engineering Managers | Reinforcement | Weekly 1:1s to review doc quality; PR reviews |
| Technical Writing Team | Subject Matter Experts | Co-design curriculum; review final projects |
| Support Team | Business Partners | Share ticket data; validate impact metrics |
| VP of Engineering | Executive Sponsor | Quarterly business reviews; celebrate wins |

---

## Templates & Job Aids Provided

1. **API Reference Template** (Markdown)
   - Endpoint description
   - Request/response examples
   - Parameters table
   - Error codes
   - Code examples (Python, JavaScript, cURL)

2. **Tutorial Template** (Step-by-step)
   - What you'll build
   - Prerequisites
   - Step 1, 2, 3... (with code snippets)
   - Troubleshooting section
   - Next steps

3. **PR Checklist** (Added to GitHub PR template)
   - [ ] Code reviewed
   - [ ] Tests pass
   - [ ] **Docs updated (or N/A)**
   - [ ] Changelog entry added

4. **Plain Language Cheat Sheet** (1-pager PDF)
   - Common jargon → Plain language alternatives
   - Active voice examples
   - Heading best practices

---

**Program Owner:** Rachel Kim, Senior Learning Experience Designer
**Technical Advisor:** Dr. Sarah Johnson, Lead Technical Writer
**Last Updated:** December 5, 2025

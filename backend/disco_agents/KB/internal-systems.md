# Internal Systems Reference

Contentful's internal tech stack for I.S. integrations.

---

## Core Business Systems

### Salesforce
**Domain**: CRM, sales pipeline, customer data
**Owner**: Revenue Operations
**API Quality**: Good - REST API, well-documented
**Common Use Cases**:
- Opportunity data for deal desk
- Account health monitoring
- Customer 360 views
**Considerations**:
- Data sensitivity: customer PII, deal terms
- Governor limits on API calls
- Sandbox available for testing

### Coupa
**Domain**: AP, procurement, vendor management
**Owner**: Finance / Procurement
**API Quality**: Moderate - some limitations
**Common Use Cases**:
- Invoice processing automation
- Vendor onboarding
- Spend analysis
**Considerations**:
- OCR issues reported with certain invoice formats
- Integration with NetSuite for GL
- Approval workflows are complex

### Workday
**Domain**: HR, payroll, employee data
**Owner**: People Team
**API Quality**: Complex - reporting can be tricky
**Common Use Cases**:
- Employee onboarding automation
- Headcount reporting
- Compensation data
**Considerations**:
- Highly sensitive PII
- Custom reports often needed
- Changes require careful testing

### NetSuite
**Domain**: Accounting, GL, financial reporting
**Owner**: Finance / Controllership
**API Quality**: Good - SuiteScript available
**Common Use Cases**:
- Financial close automation
- Revenue recognition
- Cash flow reporting
**Considerations**:
- SOX compliance requirements
- 5-day close process is sacred
- Integration with Coupa, Salesforce

### Jira
**Domain**: Ticketing, project management, workflows
**Owner**: I.S. / Engineering
**API Quality**: Excellent - REST API, webhooks
**Common Use Cases**:
- Intake workflows
- Status tracking
- Integration hub for other systems
**Considerations**:
- Standard integration patterns available
- Can get complex with custom fields
- Omnia replacing some intake functions

### LinkSquares
**Domain**: Contract management, legal
**Owner**: Legal
**API Quality**: Moderate
**Common Use Cases**:
- Contract analysis
- Vendor agreement tracking
- Obligation monitoring
**Considerations**:
- Contains sensitive legal terms
- Integration with Jira for workflows
- AI features built-in (may overlap with custom builds)

---

## AI & Productivity Tools

### Glean
**Domain**: Enterprise search, Q&A, simple agents
**Owner**: I.S.
**Capabilities**:
- Enterprise-wide search
- Q&A over company data
- Simple agent creation (team-specific)
**Limitations**:
- 128k token context window
- Best for "small problems"
- Not for complex multi-step workflows
**Use When**: Self-serve tier, simple lookups, team Q&A agents

### Claude / ChatGPT / Gemini
**Domain**: Complex AI tasks, large context problems
**Owner**: Individual / I.S. for strategic builds
**Capabilities**:
- Large context windows (200k+ tokens)
- Complex reasoning
- Code generation
- Multi-step workflows
**Use When**: Problems too big for Glean, custom agent builds

### Notebook LM / AI Studio
**Domain**: Document analysis, research
**Use When**: Deep analysis of large document sets

---

## Communication & Collaboration

### Slack
**Domain**: Messaging, notifications, workflows
**API Quality**: Excellent
**Common Use Cases**:
- Notifications from other systems
- Approval workflows
- Bot integrations
- Slash commands

### Google Workspace
**Domain**: Email, calendar, docs
**API Quality**: Good
**Common Use Cases**:
- Calendar integrations
- Document automation
- Email triggers

---

## Upcoming: Omnia

**Domain**: Procurement intake, workflow orchestration
**Status**: Implementing (3-month timeline)
**Replaces**: Current Jira intake for procurement
**Capabilities**:
- AI-powered dynamic workflows
- Slack-first interface
- Better renewal tracking
- KPI/SLA reporting

---

## Integration Risk Matrix

| System | API Quality | Data Sensitivity | Risk Level |
|--------|-------------|------------------|------------|
| Salesforce | Good | High (customer data) | Medium |
| Coupa | Moderate | Medium (financial) | Medium |
| Workday | Complex | Very High (PII) | High |
| NetSuite | Good | High (financial) | Medium |
| Jira | Excellent | Low | Low |
| LinkSquares | Moderate | High (legal) | Medium |
| Glean | Good | Varies | Low |
| Slack | Excellent | Low | Low |

---

## Data Flow Patterns

### Common Integration Patterns

**Salesforce → Slack**: Deal alerts, account updates
**Jira → Slack**: Ticket notifications, approvals
**Coupa → NetSuite**: Invoice to GL
**Workday → Slack**: Onboarding notifications
**LinkSquares → Jira**: Contract review workflows

### Data Sensitivity Tiers

| Tier | Examples | Requirements |
|------|----------|-------------|
| Public | Product docs, KB articles | None |
| Internal | Processes, policies | Auth required |
| Confidential | Customer data, financials | Role-based access |
| Restricted | PII, compensation, legal | Explicit approval, audit trail |

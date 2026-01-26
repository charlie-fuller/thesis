# Contentful Systems & Data Sources

## Purpose
Reference document for known systems, data sources, and integrations at Contentful. Use this to understand what data exists and where it lives when planning discovery or identifying integration requirements.

---

## Core Business Systems

### CRM: Salesforce
**Purpose:** Customer relationship management, sales pipeline, account data

**Key Objects:**
- Accounts (customers, prospects)
- Opportunities (deals, renewals)
- Contacts (people at accounts)
- Activities (calls, meetings, emails)

**Key Data:**
- Account health indicators
- ARR/MRR by account
- Contract details
- Sales stage and pipeline
- Account ownership

**Integration Points:**
- Marketing automation sync
- Support ticketing linkage
- Usage data enrichment

**Access:** Sales, CS, RevOps teams

---

### Support: Zendesk
**Purpose:** Customer support ticketing and help center

**Key Data:**
- Support tickets (issues, requests)
- Ticket resolution times
- Customer satisfaction scores
- Help center article usage

**Integration Points:**
- Salesforce account linkage
- Product feedback tagging
- Usage correlation

**Access:** Support, CS, Product teams

---

### Product Analytics: [TBD - Amplitude/Mixpanel/etc.]
**Purpose:** Product usage tracking and analytics

**Key Data:**
- Feature usage metrics
- User engagement patterns
- Conversion funnels
- Retention metrics

**Integration Points:**
- CRM account enrichment
- Health scoring inputs
- CS alerting

**Access:** Product, Engineering, CS teams

---

### Marketing Automation: [TBD - Marketo/HubSpot/etc.]
**Purpose:** Marketing campaigns, lead nurturing, email

**Key Data:**
- Lead scoring
- Campaign engagement
- Email metrics
- Website behavior

**Integration Points:**
- Salesforce sync
- Product-led signals
- Event attendance

**Access:** Marketing, Sales teams

---

### Finance: [TBD - NetSuite/etc.]
**Purpose:** Financial systems, billing, invoicing

**Key Data:**
- Invoices and payments
- Revenue recognition
- Contract financials
- Forecast data

**Integration Points:**
- Salesforce opportunity sync
- Usage-based billing

**Access:** Finance, RevOps teams

---

## Data & Analytics Infrastructure

### Data Warehouse: [TBD - Snowflake/BigQuery/etc.]
**Purpose:** Centralized data storage and analytics

**Key Capabilities:**
- Cross-system data joins
- Historical trend analysis
- Custom reporting
- ML/AI data source

**Key Tables/Datasets:**
- [To be documented]

**Access:** Data team, analysts with permissions

---

### BI Tools: [TBD - Looker/Tableau/etc.]
**Purpose:** Business intelligence and dashboards

**Key Dashboards:**
- [To be documented]

**Access:** Varies by dashboard

---

## Communication & Collaboration

### Slack
**Purpose:** Internal communication, notifications

**Key Integrations:**
- Salesforce alerts
- Support ticket notifications
- Deployment alerts

---

### Google Workspace
**Purpose:** Email, documents, calendar

**Key Data:**
- Meeting schedules
- Shared documents
- Email communications

---

## Known Data Gaps

| Gap | Impact | Notes |
|-----|--------|-------|
| [To be identified during discovery] | | |

---

## System Owners

| System | Owner/Team | Contact |
|--------|-----------|---------|
| Salesforce | RevOps | [TBD] |
| Zendesk | Support Ops | [TBD] |
| Data Warehouse | Data Engineering | [TBD] |

---

## Notes for Discovery

When planning discovery for initiatives involving systems:

1. **Identify system touchpoints early** - Which systems does the initiative interact with?
2. **Find system owners** - Who knows the data and can validate assumptions?
3. **Assess data quality** - Is the data reliable? How current?
4. **Understand access patterns** - Who can see what? Are there restrictions?
5. **Map integration points** - How do systems talk to each other today?

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-22 | Initial template - needs enrichment from system owners |

---

*Note: This document is a starting template. Enrich with actual system details during discovery sessions with system owners and data teams.*

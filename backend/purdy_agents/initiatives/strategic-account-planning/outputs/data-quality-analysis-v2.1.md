# Data Quality Analysis: Strategic Account Planning v2.1

## Summary

Data quality emerged as the dominant theme across all discovery sessions. The core finding is that data exists across multiple systems but is fragmented, inconsistent, and often stale. AI automation cannot solve underlying data quality issues—"bad data is bad outputs" (Tyler). This analysis catalogs specific data issues by system, identifies root causes, and recommends remediation priorities.

---

## Data Issue Categories

### Category 1: External Data Source Staleness

**Problem:** Third-party data sources contain outdated or obsolete information that requires manual verification.

**Specific Examples:**
- "I tried to do Spark and their subsidiaries with ChatGPT and I found that its answer, but nine out of the 10 were obsolete and spun off already." - Workshop discussion
- "The J and J example I gave, the link that ChatGPT pulls actually kicks back to a more consolidated lake now, so while it still exists, it's not really operational." - Matt Vosberg
- "We may also see something that isn't across Crossbeam is not a catch all. It's just who has crossbeam and who's partnered with us to reveal those things." - Matt Vosberg

**Affected Systems:**

| System | Data Type | Specific Issue |
|--------|-----------|----------------|
| ZoomInfo | Company subsidiaries, org structure | "Nine out of ten were obsolete" |
| ChatGPT (standard mode) | Company research | Returns outdated acquisitions/spinoffs |
| Crossbeam | Partner relationships | Incomplete - not all partners use it |
| LinkedIn Sales Navigator | Org charts, contacts | Varies by company/region; Germany especially weak |

**Root Cause:** External data vendors update at different cadences; M&A activity creates rapid obsolescence; AI models have training cutoffs.

---

### Category 2: Fragmented Internal Views

**Problem:** No single view of customer product usage; requires navigating multiple systems and Tableau dashboards.

**Specific Examples:**
- "It seems to be split up into multiple views. Which some views have 80% information, and then you got to go to at least one or two other views." - Tom Woodhouse
- "I don't think there's one Tableau V that tells the whole story." - Tom Woodhouse
- "Tableau overall kind of navigation, get through a tableau or to figure out everything you potentially look at is just not the greatest UI." - Tom Woodhouse

**Affected Systems:**

| System | Data Type | Specific Issue |
|--------|-----------|----------------|
| Tableau | Product usage, space count, health metrics | Split across multiple views; no unified dashboard |
| Salesforce | Account data, opportunities, contacts | Fields populated inconsistently |
| Gatekeeper | Content types, space usage | Limited visibility into features/products |
| Granulate | Internal knowledge | AEs don't know to look here |

**Root Cause:** Systems built for different purposes; no cross-system aggregation layer; BI evolved organically.

---

### Category 3: Missing Field-Level Data

**Problem:** Specific fields needed for account planning are not reliably captured or accessible.

**Specific Examples:**
- "The gap on that, I would say, is what are the sites and use cases? Where do you think that's gathered? A lot of times you're going off of naming conventions and orgs and maybe QBRs that we've had. So sitting in a deck. But that information is not aggregated or surfaced." - Matt Vosberg
- "One of the things we called out... monthly active profiles. We were looking at getting Sunrush to be able to audit that site to be able to provide it to us." - Steve Letourneau (data doesn't exist)
- "You don't necessarily have to duplicate that information in Salesforce. You just give, like, a window. How to view it, I guess, whereas the information." - Tom Woodhouse (surfacing vs. storage)

**Affected Fields:**

| Field | Source | Specific Issue |
|-------|--------|----------------|
| Monthly Active Profiles (MAPs) | Not captured | Critical for personalization sizing; considering Semrush |
| Sites/Use Cases | QBR decks, tribal knowledge | "Not aggregated or surfaced" |
| Delivery Architecture/Hosting | BuiltWith (partial) | Needed for Vercel co-sell; not systematically captured |
| Current CMS | BuiltWith, manual | "Just a blob" - needs parsing |
| Frontend Framework | BuiltWith, manual | Not consistently captured |

**Root Cause:** Fields defined for CMS sales, not account planning; personalization metrics never systematized; "tribal knowledge" not codified.

---

### Category 4: Access Restrictions

**Problem:** AEs cannot self-serve certain data sources; must go through gatekeepers.

**Specific Examples:**
- "AEs don't have direct access to Crossbeam... we'd have to go through the PMs." - Matt Vosberg
- "I don't think a lot of folks from the field have access to Gatekeeper or Tableau." - Meron
- "There's kind of like a gatekeeping to partner information that's available to us right now." - Matt Vosberg

**Affected Access:**

| System | Who Has Access | Who Needs Access | Gatekeeping Issue |
|--------|----------------|------------------|-------------------|
| Crossbeam | Partner Managers only | AEs | Must request partner data per account |
| Gatekeeper | Limited | AEs, SEs | Product usage insights locked away |
| Tableau | Technical users | Field team | Navigation complexity is a barrier |

**Root Cause:** Licensing/cost decisions; historical access patterns; complexity barrier ("not the greatest UI").

---

### Category 5: Data Quality in Source Systems

**Problem:** Even when data exists, it may be stale, incomplete, or incorrectly entered.

**Specific Examples:**
- "We can't go back and fix all the garbage that has been put into Salesforce in the improper way that people have been updating it previously." - Tyler
- "It's like, it's trust but verify. Doesn't mean it doesn't exist, or we just haven't entered it. I think it's probably a big part of the conversation. Is it something that's fallen through the cracks where we do know, or do we just not know?" - Matt Vosberg
- "Bad data is bad outputs. There's no getting around that." - Tyler

**Affected Systems:**

| System | Quality Issue |
|--------|---------------|
| Salesforce | Inconsistent field completion; "garbage" from improper updates |
| BuiltWith (Salesforce field) | "Just a blob" - unstructured text, not parsed |
| Crossbeam | Stale relationships; not everyone updates |

**Root Cause:** No enforcement of data entry standards; historical data debt; no cleanup initiative.

---

## Systems Inventory

| System | Data Provided | Limitations | Quote |
|--------|---------------|-------------|-------|
| Salesforce | Accounts, opportunities, contacts, partner data | Inconsistent completion; "garbage" data | "We can't go back and fix all the garbage" - Tyler |
| Tableau | Product usage, space count, health | Split across multiple views; no unified dashboard | "No single Tableau V tells the whole story" - Tom Woodhouse |
| BuiltWith | Tech stack detection | "Just a blob" in Salesforce; needs parsing | "That blob built with that I referenced" - Matt Vosberg |
| ZoomInfo | Company data, contacts, org charts | Often obsolete | "Nine out of ten were obsolete" - Workshop |
| Crossbeam | Partner relationships | AEs no direct access; incomplete coverage | "Not everybody has crossbeam" - Matt Vosberg |
| Gatekeeper | CF product usage, content types | Limited field access; no feature/product detail | "Doesn't give us visibility into features, products" - Meron |
| Glean | Internal knowledge aggregation | Depends on underlying data quality | "If we don't have the data correct in Glean we're going to waste" - Tyler |
| ChatGPT/Gemini | External research | Standard mode unreliable; Deep Research better | "Deep Research about 99% accurate" - Matt Lazar |
| LinkedIn Sales Nav | Contacts, org charts | Varies by region; weak in Germany | "Lower uptake of LinkedIn in Germany" - Thomas |

---

## Root Cause Analysis

### Why do these data issues exist?

1. **Systems built for different purposes:** Salesforce for pipeline, Tableau for reporting, Gatekeeper for product—none designed for holistic account planning.

2. **No data governance for account planning fields:** Nobody owns "sites and use cases" or "monthly active profiles" as required fields.

3. **AI can't fix bad data:** "AI is only as good as the data" - automation amplifies problems rather than solving them.

4. **Access patterns driven by cost/licensing:** Crossbeam, Gatekeeper access limited to certain roles.

5. **Organic growth without consolidation:** "A lot of the basic stuff of data aggregation... the issue for us was for Rich and I, if we had to come into a mirror board, where do we actually go?" - Steve Letourneau

6. **No cleanup initiative:** Unlike JP Morgan ("started cleaning their data for AI six years ago" - Tyler), Contentful hasn't invested in data hygiene.

---

## Recommendations

| Issue | Recommendation | Owner | Priority |
|-------|----------------|-------|----------|
| Fragmented Tableau views | Build unified product usage dashboard | BI Team | High |
| BuiltWith "blob" | Parse into structured fields (CMS, Frontend, Personalization) | Data Team | High |
| No MAPs data | Evaluate Semrush or equivalent for profile estimation | Steve/Sales Ops | Medium |
| Crossbeam access | Create curated partner intelligence export for Glean agent | Partner Team/Dean | Medium |
| Sites/Use Cases not captured | Add required field to CSM account review process | CSM Leadership | Medium |
| Salesforce data quality | Define minimum required fields for strategic accounts; enforce at QBR | Sales Ops | Medium |
| Gatekeeper access | Evaluate expanding access OR building agent to surface data | IT | Low |
| ZoomInfo staleness | Use as supplement to Deep Research, not primary source | AE training | Low |

---

## Data Quality Improvement Prerequisites

Before AI automation can be effective, these data foundations must be in place:

1. **Unified Tableau View:** Single dashboard with space count, usage trends, health indicators
2. **BuiltWith Parsing:** Structured fields extracted from blob text
3. **MAPs Estimation:** Method to estimate personalization opportunity size
4. **Partner Intelligence Export:** Clean, Glean-accessible partner data
5. **Minimum Field Standards:** Defined and enforced for strategic accounts

"The culmination that I'm hearing is that Salesforce is the only thing for them. It's the only thing internally." - Tyler

Any solution must ultimately feed into/from Salesforce as the system of record.

---

*Generated using PuRDy v2.1 Data Quality Lens*

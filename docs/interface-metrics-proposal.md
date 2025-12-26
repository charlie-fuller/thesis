# Thesis Interface Metrics & KPI Proposal

**Date:** December 15, 2025
**Author:** Paige Bradbury
**Purpose:** Dashboard metrics to track interface friction and user experience quality

---

## Executive Summary

Based on December 15, 2025 user session analysis, we've identified 5 critical friction points in the Thesis interface that are impacting user productivity and satisfaction. This document proposes specific KPIs and dashboard metrics to track, diagnose, and prioritize improvements.

---

## Friction Point #1: File Upload Failures

### What Happened
User attempted to upload PDF file. System failed and blocked the entire chat session until the file was manually deleted.

### User Impact
- Complete workflow interruption
- Frustration and lost productivity
- No alternative path to share content

### Proposed KPIs

| Metric | Definition | Target |
|--------|------------|--------|
| **File Upload Success Rate** | % of successful uploads vs. attempts | >95% |
| **File Upload Error Recovery Time** | Seconds until user can continue after failure | <10s |
| **Blocked Session Rate** | % of sessions where user couldn't proceed due to file issues | <2% |
| **File Type Failure Distribution** | Which file types fail most often | Track all types |

### Dashboard Display
```
File Upload Health
├─ Success Rate: 45% ← CRITICAL
├─ Most Failed Type: PDF (78% failure rate)
├─ Avg Recovery Time: 3.2 minutes
└─ Sessions Blocked: 15% this week
```

---

## Friction Point #2: Cognitive Overload (Output Length)

### What Happened
Thesis generated entire training program (Phases 1-3, dashboard specs, facilitation guides, success criteria) in single response. User had no opportunity to validate direction before significant output investment.

### User Impact
- Information overwhelm
- Cannot validate approach incrementally
- Violates Thesis's own DOSE principles
- Even experienced instructional designers report feeling overwhelmed

### Proposed KPIs

| Metric | Definition | Target |
|--------|------------|--------|
| **Response Length** | Words/tokens per response | <500 words for initial concepts |
| **Validation Request Rate** | % of complex outputs that ask "Does this direction work?" before elaborating | >80% |
| **User Overwhelm Signals** | Count of phrases: "too much," "just outline," "start over" | Trend toward 0 |
| **Progressive Disclosure Adoption** | % of complex outputs using cascading reveal | >80% |

### Dashboard Display
```
Cognitive Load Management
├─ Avg Response Length: 2,847 words ← [CRITICAL] 5.7x above target
├─ Validation-Before-Elaboration: 12% ← [CRITICAL] Should be 80%+
├─ User Overwhelm Signals: 3 detected this session
└─ Progressive Disclosure Used: 0% ← [CRITICAL] Protocol not implemented
```

---

## Friction Point #3: UI Formatting Issues

### What Happened
- `<br>` tags appearing in output instead of actual bullet points
- Dense text blocks with poor visual hierarchy
- Difficult to scan information quickly

### User Impact
- Reduced readability
- User must reformat content to parse it
- Violates `<visual_first_design>` guidelines

### Proposed KPIs

| Metric | Definition | Target |
|--------|------------|--------|
| **Markdown Rendering Errors** | Count of `<br>` tags, malformed bullets, broken formatting | <5 per session |
| **Visual Hierarchy Score** | Proper use of headers, bullets, tables, whitespace (0-100) | >85 |
| **User Readability Actions** | Did user request reformatting or copy/paste elsewhere? | <10% |
| **Table vs. Paragraph Ratio** | Using scannable formats per guidelines | >40% for data/comparisons |

### Dashboard Display
```
Output Formatting Quality
├─ Markdown Errors: 14 instances ← [WARNING] `<br>` tags, broken bullets
├─ Visual Hierarchy Score: 62/100 ← [WARNING] Below target
├─ Table Usage: 18% (target: 40%)
└─ User Reformatting Requests: 1 this session
```

---

## Friction Point #4: Permission Request Failures

### What Happened
"Stream closed" error when attempting to write files. Permission dialog timed out or failed before user could approve.

### User Impact
- Cannot complete tasks
- Requires manual retry
- Breaks flow state

### Proposed KPIs

| Metric | Definition | Target |
|--------|------------|--------|
| **Permission Request Success Rate** | % of approved vs. failed/timeout requests | >90% |
| **Permission Timeout Rate** | How often dialogs close before user responds | <10% |
| **Retry Attempts per Task** | How many times user must approve same action | <1.2 |
| **Average Permission Response Time** | Seconds between request and user action | Track baseline |

### Dashboard Display
```
Permission System Health
├─ Approval Success Rate: 67% ← [WARNING] 33% timeout/failure
├─ Timeout Rate: 25% ← [CRITICAL] Above threshold
├─ Avg Retries per Task: 1.8
└─ User Response Time: 4.2s (normal)
```

---

## Friction Point #5: Iterative Workflow Interruptions

### What Happened
User wanted to iterate on system instructions incrementally. Workflow repeatedly interrupted by permission failures, git configuration issues, stream errors.

### User Impact
- Slowed creative iteration
- Increased cognitive switching
- Reduced productive work time

### Proposed KPIs

| Metric | Definition | Target |
|--------|------------|--------|
| **Task Completion Rate** | % of tasks completed without interruption | >85% |
| **Context Switches** | Number of times user had to stop and fix tooling | <2 per session |
| **Time to First Value** | Minutes until user sees useful output after request | <2 min |
| **Workflow Efficiency Score** | Ratio of productive work vs. troubleshooting | >80/20 |

### Dashboard Display
```
Workflow Efficiency
├─ Task Completion (No Interruption): 40% ← [CRITICAL] Below target
├─ Context Switches: 5 ← [CRITICAL] (file permission, git config, stream errors)
├─ Time to First Value: 12 minutes ← [CRITICAL] Target: <2 min
└─ Productive vs. Troubleshooting: 60/40 ← [WARNING] Target: 80/20
```

---

## Proposed Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Thesis Interface Health Dashboard - Session Analysis        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ CRITICAL ISSUES                                              │
│ ├─ File Upload Failure Rate: 78% (PDFs)                     │
│ ├─ Progressive Disclosure: 0% adoption                       │
│ └─ Permission Timeout: 25% of requests                       │
│                                                              │
│ MODERATE ISSUES                                              │
│ ├─ Markdown Rendering Errors: 14 instances                  │
│ ├─ Cognitive Load: Avg 2,847 words (5.7x target)            │
│ └─ Task Interruptions: 5 context switches                    │
│                                                              │
│ WORKING WELL                                                 │
│ ├─ User Response Time: 4.2s (normal)                        │
│ └─ Git Integration: Successfully committed                   │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ PRIORITY RECOMMENDATIONS                                     │
│ 1. [P0] Fix PDF upload handling (immediate user blocker)    │
│ 2. [P0] Implement progressive disclosure enforcement        │
│ 3. [P1] Fix markdown rendering (backend or frontend)        │
│ 4. [P1] Improve permission request reliability              │
│ 5. [P1] Add user overwhelm detection                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Tracking Strategy

### Leading Indicators (Predict Problems)
- Response length before user confirmation
- Frequency of validation questions
- Permission request timeout trends
- File upload attempt patterns

### Lagging Indicators (Measure Impact)
- User frustration signals ("this is too much," file deletion, retries)
- Task abandonment rate
- Session efficiency (productive time vs. troubleshooting)
- Feature adoption (progressive disclosure, proper formatting)

### North Star Metrics (Success Criteria)
- **80%+** of complex outputs use progressive disclosure
- **<5%** file upload failure rate
- **90%+** markdown rendering accuracy
- **<10%** permission request failures
- **User overwhelm signals approaching zero**

---

## Implementation Recommendations

### Phase 1: Data Collection (Week 1-2)
- Instrument backend to capture all proposed metrics
- Add logging for user friction signals
- Establish baseline measurements

### Phase 2: Dashboard Development (Week 3-4)
- Build real-time dashboard with proposed layout
- Alert system for critical thresholds
- Weekly report generation

### Phase 3: Continuous Improvement (Ongoing)
- Weekly review of metrics
- Prioritize fixes based on user impact
- A/B test solutions
- Iterate on thresholds as product matures

---

## Expected Outcomes

**Short-term (1 month):**
- Visibility into top friction points
- Data-driven prioritization of fixes
- Baseline metrics established

**Medium-term (3 months):**
- 50% reduction in critical issues
- Improved user satisfaction scores
- Faster task completion times

**Long-term (6 months):**
- All metrics hitting target thresholds
- Proactive issue detection
- User experience excellence

---

## Next Steps

1. Review and approve proposed metrics
2. Assign engineering resources for instrumentation
3. Define data pipeline and storage
4. Build dashboard MVP
5. Pilot with selected user sessions
6. Refine based on feedback

---

**Document Status:** Ready for Review
**Next Review Date:** TBD after Charlie's feedback

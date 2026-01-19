# Dashboard Analytics

This guide explains how to use the admin dashboard to monitor platform usage, track KPIs, and analyze user engagement through the Bradbury Impact Loop methodology.

## Accessing the Dashboard

Navigate to **Dashboard** (first item in admin navigation) to open the **Admin Dashboard**.

The dashboard provides three main views via tabs:
- **Overview** - Quick stats and recent activity
- **KPI Dashboard** - Bradbury Impact Loop metrics
- **Usage Analytics** - Detailed usage patterns

## Overview Tab

The **Overview** tab provides at-a-glance platform health.

### Quick Stats

Four color-coded metric cards display:

- **Total Users** - Number of registered user accounts
- **Conversations** - Total conversation count across all users
- **Documents** - Number of uploaded and processed documents
- **Messages** - Total message count (user + assistant messages)

These stats update in real-time as the platform is used.

### System Health Panel

The **System Health** panel monitors the status of all platform services in real-time:

#### Service Status Indicators

Each service shows a status with color coding:
- **Green** - Service is operational and responding normally
- **Blue** - Service is idle (no recent requests, but available)
- **Yellow** - Service is degraded or slow
- **Red** - Service is down or experiencing errors

#### Monitored Services

**Supabase (Database)**
- Shows connection status and response time
- Displays: Fast (≤100ms), Good (≤300ms), or Slow (>300ms)
- Critical service - if down, platform cannot function

**Railway (Backend API)**
- Shows deployment status: Running, Deploying, or Error
- Critical service - handles all API requests

**Anthropic (Claude LLM)**
- Powers all chat responses
- Shows "Idle" when no recent requests
- Shows "Active" with latency when processing
- Latency displayed in seconds (e.g., "Active (1.2s)")

**Voyage AI (Embeddings)**
- Generates vector embeddings for document search
- Shows "Idle" when no recent indexing or search
- Used for document processing and help system

#### Overall Status

The panel header shows overall system health:
- **All Operational** (green) - All critical services running
- **Degraded Performance** (yellow) - Some services slow or auxiliary services down
- **Down** (red) - Critical services (Supabase or Railway) are failing

Hover over any service card for a tooltip explaining what that service does.

### Interface Health Panel

The **Interface Health** panel monitors user-facing feature performance:

#### Upload Success Rate

Shows document upload reliability over the last 24 hours:
- **Green (≥95%)** - Uploads working normally
- **Yellow (85-95%)** - Some upload failures occurring
- **Red (<85%)** - Significant upload problems

Also displays the count of failed uploads in the period.

#### Image Generation

Tracks AI image generation feature usage over 7 days:
- **Generated** - Number of images actually created
- **Suggested** - Times Thesis offered to create an image

This helps understand if users are accepting image suggestions.

#### Average Response Length

Monitors Thesis's response verbosity:
- **Green (≤500 words)** - Concise, focused responses
- **Yellow (500-800 words)** - Responses getting lengthy
- **Red (>800 words)** - Responses too verbose

Target is ≤500 words for optimal user experience.

#### Stuck Conversations

Identifies conversations waiting for user action:
- Shows count of conversations stuck >5 minutes awaiting image confirmation
- **Green (0)** - No stuck conversations
- **Yellow (1-2)** - Some conversations may need attention
- **Red (3+)** - Multiple stuck conversations

Also shows average turns to reach useable output.

#### Issues Requiring Attention

When problems exist, an expandable section shows:
- **Stuck Documents** - Files stuck in processing for too long
- **Recent Failures** - Documents that failed to process with error details

## KPI Dashboard Tab

The **KPI Dashboard** tab displays the Bradbury Impact Loop KPIs - specialized metrics for measuring learning and development effectiveness.

### Filtering by User

At the top, a dropdown labeled **Show metrics for:** allows filtering:
- **All Users** - Aggregate metrics across everyone
- Individual user names - Focus on specific user performance

### Ideation Velocity

The **Ideation Velocity** card measures creative output and idea generation:
- Tracks how quickly users generate and explore ideas
- Higher velocity indicates active engagement
- Useful for assessing brainstorming effectiveness

### Correction Loop

The **Correction Loop** card tracks iterative refinement:
- Measures how users improve their work through feedback cycles
- Shows engagement with the revision process
- Indicates learning through iteration

### Correction Loop Efficiency Over Time

The **Correction Loop Efficiency Over Time** panel provides trend visualization:
- Shows how correction loop patterns change over time
- Helps identify improvements in user efficiency
- Reveals trends in learning progression

### Keyword Trends

The **Keyword Trends** card shows topic patterns:
- Identifies frequently discussed subjects
- Reveals common themes in conversations
- Helps understand user focus areas

## Usage Analytics Tab

The **Usage Analytics** tab provides comprehensive usage data.

### Understanding Usage Patterns

The analytics show:
- Usage frequency over time
- Peak usage periods
- User engagement levels
- Platform utilization trends

### Interpreting Trends

Look for patterns like:
- Regular usage indicates healthy adoption
- Declining trends may suggest engagement issues
- Spikes may correlate with events or campaigns

## The Bradbury Impact Loop

Understanding the underlying methodology helps you interpret dashboard metrics effectively.

### What is the Bradbury Impact Loop?

The Bradbury Impact Loop is a learning and development framework that measures:

1. **Ideation** - Generating ideas and exploring possibilities
2. **Correction** - Refining and improving through feedback
3. **Velocity** - Speed of progress and iteration
4. **Impact** - Measurable outcomes and improvements

### Why These Metrics Matter

**Ideation Velocity** reveals:
- User creativity and engagement
- Willingness to explore new ideas
- Platform effectiveness for brainstorming

**Correction Loop** shows:
- Learning through iteration
- Quality improvement processes
- User responsiveness to feedback

**Trends Over Time** indicate:
- Skill development patterns
- Long-term engagement health
- Program effectiveness

## Using Metrics for Decision-Making

### Identifying High Performers

1. Switch to **KPI Dashboard** tab
2. Review individual users via **Show metrics for:** dropdown
3. Look for:
   - High Ideation Velocity
   - Strong Correction Loop engagement
   - Consistent improvement trends

### Spotting Engagement Issues

Warning signs include:
- Declining Ideation Velocity
- Low Correction Loop activity
- Flat or downward trends

Actions to take:
1. Review affected user's conversations
2. Check if they have appropriate documents mapped
3. Consider reaching out about platform experience

### Measuring Program Success

For overall program assessment:
1. Use **All Users** view
2. Track aggregate metrics over time
3. Look for:
   - Growing Total Users
   - Increasing message counts
   - Positive trend lines in KPIs

### Reporting Insights

When preparing reports:
1. Note key stats from **Overview**
2. Highlight KPI trends from **KPI Dashboard**
3. Include usage patterns from **Usage Analytics**
4. Compare time periods for progress assessment

## Common Analytics Tasks

### Getting a Quick Platform Status

1. **Dashboard** → **Overview** tab
2. Review **Quick Stats** cards
3. Check **Recent Activity** for latest events
4. Identify any unusual patterns

### Checking Specific User Performance

1. **Dashboard** → **KPI Dashboard** tab
2. Use **Show metrics for:** dropdown
3. Select the user's name
4. Review their individual metrics

### Tracking Monthly Progress

1. **Dashboard** → **Usage Analytics** tab
2. Review trend charts
3. Note patterns in usage frequency
4. Compare to previous periods

### Identifying Most Active Users

1. **Dashboard** → **Overview** tab
2. Note total message counts
3. Navigate to **KPI Dashboard**
4. Filter by individual users
5. Compare activity levels

### Preparing Executive Summary

1. Capture **Quick Stats** numbers
2. Note significant trends from **KPI Dashboard**
3. Identify key user segments
4. Document improvement opportunities

## Understanding the Data

### What's Being Measured

The dashboard tracks:
- User account data (counts, creation dates)
- Conversation data (count, messages, timestamps)
- Document data (uploads, processing status)
- Interaction patterns (message flow, response patterns)

### Time Periods

Different metrics may show:
- Point-in-time counts (current totals)
- Historical trends (change over time)
- Rolling averages (smoothed patterns)

### Data Freshness

Dashboard data typically:
- Updates in real-time for counts
- May have slight delays for aggregated metrics
- Reflects current database state

## Best Practices

### Regular Monitoring

1. Check dashboard daily for quick status
2. Review KPIs weekly for trends
3. Analyze usage patterns monthly for reporting

### Setting Benchmarks

1. Document baseline metrics when starting
2. Set targets for improvement
3. Track progress against goals

### Acting on Insights

When metrics indicate issues:
1. Investigate root causes
2. Take corrective action
3. Monitor for improvement
4. Document learnings

### Sharing Results

1. Export or screenshot key metrics
2. Prepare regular reports for stakeholders
3. Highlight successes and opportunities
4. Recommend actions based on data

## Troubleshooting Dashboard Issues

### Stats Showing Zero

If counts show zero unexpectedly:
1. Check database connectivity
2. Verify data exists (users, conversations)
3. Refresh the page
4. Contact technical support if persistent

### Trends Not Loading

If trend charts don't display:
1. Wait for page to fully load
2. Check for JavaScript errors (browser console)
3. Try a different browser
4. Clear browser cache and reload

### Metrics Seem Incorrect

If numbers don't match expectations:
1. Verify time period settings
2. Check filter selections
3. Compare with source data
4. Document discrepancy for investigation

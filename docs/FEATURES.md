# AI GrowthPilot — Complete Feature Documentation

## Overview of Core Modules

AI GrowthPilot provides an integrated growth engine across 8 core functional modules:

---

### 1. Overview Dashboard (`/`)

The command center presents an executive summary of marketing performance and AI operations:

- **Top KPI Cards**:
  - `Total Leads`: Total imported prospect records with month-over-month velocity.
  - `Qualified Leads`: Percentage and count of leads meeting high-priority ICP criteria.
  - `Active Campaigns`: Number of live multi-channel campaigns.
  - `Content Scheduled`: Volume of posts in the calendar queue.
  - `Average Lead Score`: Objective numerical index (0–100) reflecting portfolio quality.
- **Interactive Recharts Visualizations**:
  - *Lead Acquisition Velocity*: 6-month dual-area chart comparing total leads against qualified opportunities.
  - *Pipeline Attribution*: Donut chart illustrating lead acquisition by channel (Website, LinkedIn, Referrals, etc.).
  - *Campaign Performance*: Multi-bar chart contrasting impressions, clicks, and captured leads across active campaigns.
  - *Qualification Distribution*: Pie chart showing the ratio of High, Medium, and Low priority prospects.
- **Priority Prospect Queue**: Instant table of the highest-scoring leads with one-click inspection.
- **AI Growth Recommendations**: Context-aware tactical suggestions based on active pipeline gaps.
- **Recent AI Activities**: Live activity stream showing completed strategy generations, campaign drafts, and scoring runs.
- **Demonstration Notice**: High-visibility banner disclosing that the data is seeded for the demo company "NovaTech Solutions".

---

### 2. AI Growth Strategy (`/strategy`)

The strategic brain of the application formulating 30-day go-to-market roadmaps:

- **Business Profile Form**:
  - Company name, industry, website URL.
  - Core business description.
  - Dynamic tag lists for services, target audiences, and target geographies (Australia, United States, India).
  - Monthly marketing budget slider/input.
  - Primary objective and known competitor inputs.
- **"Generate Growth Strategy" Engine**:
  - Communicates with Gemini 2.5 Flash to synthesize 10 structured sections:
    1. *Executive Summary*: High-level strategy synthesis.
    2. *Ideal Customer Profiles (ICPs)*: Persona titles, company profile criteria, core needs, and buying triggers.
    3. *Target Market Insights*: Macro observations on tech buyer behavior.
    4. *Customer Pain Points*: Specific operational bottlenecks prospects face.
    5. *Unique Value Proposition (UVP)*: High-impact differentiation statement.
    6. *Marketing Objectives*: Measurable milestone targets with explicit timelines.
    7. *Recommended Channels*: Percentage budget allocation and tactical rationale.
    8. *Campaign Recommendations*: Specific tactical campaigns to launch.
    9. *Suggested KPIs*: Metrics, target thresholds, and tracking frequencies.
    10. *30-Day Phased Action Plan*: Phased roadmap from Days 1-7 through Days 22-30.
    11. *Model Assumptions & Uncertainty Disclosures*: Transparent disclosure of assumed contract sizes and baseline sales cycle metrics.
- **Visual Source Badging**: Displays `Gemini AI` (emerald badge) for authentic model completions or `Demo Simulation` (amber badge) for deterministic simulations.
- **Decoupled 3-State AI & Error Recovery**: If the live Gemini API fails (invalid key or quota limit), the UI presents an explicit error banner with a one-click button to **"Generate in Demo Mode Instead"** &mdash; preventing silent fallbacks to fake data.
- **Interactive Capabilities**:
  - Individual section regeneration without re-running the entire prompt.
  - Strategy version history selector.
  - Profile state persistence in SQLite.

---

### 3. Campaign Studio (`/campaigns`)

A multi-channel marketing generation studio producing platform-native collateral:

- **Campaign Brief Builder**:
  - Inputs for campaign name, product/service, target audience, objective, tone of voice, key value props, and call-to-action.
  - Supported Channels: **LinkedIn**, **Instagram**, **Email Marketing**, **Google Search Ads**, **Landing Page Copy**.
- **Generated Package**:
  - *Strategic Overview & Narrative Anchor*: Thesis explaining audience psychology.
  - *Visual Source Pill*: Clearly demarcates `Gemini AI` vs `Demo Simulation`.
  - *3 Distinct Headline Variations*: Benefit-driven, curiosity/pain-point, and direct commercial hooks with one-click copy.
  - *3 Multi-Angle Content Variations*:
    - Variation A: Problem-Agitate-Solve.
    - Variation B: Quantifiable Transformation & ROI.
    - Variation C: Contrarian Thought Leadership.
  - *Inline Copy Editing*: Modal allowing marketers to tailor generated copy before saving.
  - *Audience Segmentation Parameters*: Targeting guidance for media buyers.
  - *Hashtag Palette*: Channel-optimized hashtag suggestions.
  - *Visual Campaign Schedule*: Timeline mapping publication cadence across the week.
- **Campaign Management & Error Handling**:
  - Save, edit, and delete campaigns.
  - Dedicated error banner with one-click option to generate via Demo Simulation upon API failure.
  - Campaign selector dropdown for historical review.

---

### 4. Content Calendar (`/calendar`)

A content planning and approval workspace:

- **Calendar Views**:
  - *List View*: Detailed view with full draft copy, tags, and workflow status dropdowns.
  - *Timeline View*: Card-based chronological display by scheduled publication date.
- **Multi-Channel Coverage**: Filter posts by LinkedIn, Instagram, Blog, Email, or Google Ads.
- **Human-in-the-Loop Workflow**:
  - Statuses: `Draft` &rarr; `Pending Approval` &rarr; `Approved` &rarr; `Published (Simulated)`.
  - Enforces review before any content is marked approved.
- **"Generate 7-Day Content Plan"**:
  - AI synthesizes a week-long multi-channel trajectory designed to build authority, present technical case studies, and drive discovery calls.
  - Explicit error handling offering instant Demo Simulation fallback if API call fails.
- **Manual Post Scheduling**: Add bespoke posts with datetime pickers and tag sets.

---

### 5. Lead Intelligence (`/leads`)

An explainable lead qualification and account-based management module:

- **CSV Import System & Security**:
  - Drag-and-drop file upload with strict 5MB file cap (`MAX_CSV_BYTES`).
  - Automatic column header synonym mapping (`job_title` &rarr; `Role`, `company_name` &rarr; `Employer`, etc.) prioritized to prevent column collisions.
  - Case-insensitive duplicate email detection preventing double-counting.
  - RFC 5322 regex email validation isolating malformed addresses into an `errors` summary.
  - Clear import summary: total rows, successful imports, duplicate count, and parsing error feedback.
- **Explainable AI Lead Scoring**:
  - Objective 0–100 score calculated via transparent 5-factor rubric:
    1. *Industry Alignment (30%)*: Target sector match.
    2. *Decision-Maker Authority (25%)*: Job title seniority (C-level, VP, Director vs. IC).
    3. *Geographic Match (20%)*: Australia, US, and India prime market alignment.
    4. *Company Size Viability (15%)*: Mid-market (51-200) sweet-spot sizing.
    5. *Source Intent (10%)*: Inbound/Demo request vs. cold outbound.
  - Priority Categorization: `High Priority` (75–100), `Medium Priority` (50–74), `Low Priority` (0–49).
- **Slide-Over Lead Dossier**:
  - Visual factor breakdown with score pills and explanatory rationale.
  - Potential Business Fit summary.
  - Suggested Next Action prescription.
  - "Re-score AI" button with instant recovery option to score via deterministic demo rubric if API fails.
  - Pipeline Stage updater (`New`, `Contacted`, `In Discussion`, `Qualified`, `Disqualified`).
  - Internal team notes thread.
- **Sanitized CSV Export (CWE-1236 Defense)**:
  - One-click download of all stored leads formatted as CSV.
  - Automatically neutralizes formula prefixes (`=`, `+`, `-`, `@`, `\t`, `\r`) with single quotes `'` to prevent DDE spreadsheet exploits.

---

### 6. Growth Analytics (`/analytics`)

Real-time business intelligence aggregating stored database records:

- Key performance indicators: Total leads, qualified leads, qualification rate (%), average score, active campaigns.
- Target industry bar chart (horizontal orientation for readable labels).
- Regional distribution bar chart (Australia, US, India, Global).
- Lead acquisition source distribution.
- Campaign conversion attribution table: impressions, clicks, leads captured, and CTR.
- Monthly operational activity breakdown.
- Honest disclaimer confirming all metrics reflect database records.

---

### 7. Prompt Engineering Lab (`/prompt-lab`)

A showcase of prompt engineering rigor and transparency:

- **Documented Iterative Evolution**:
  - Detailed side-by-side comparison of **Version 1.0 (Baseline)**, **Version 2.0 (Refined)**, and **Version 3.0 (Production Grade)**.
  - Documented explanation of why explicit role definition, schema enforcement, and anti-hallucination guardrails improve output quality.
- **Template Registry**:
  - Browse prompt templates across Business Strategy, Campaign Generation, Content Creation, and Lead Scoring.
  - Inspect exact system instructions and user prompt templates with variable tokens.
- **Execution Audit History**:
  - Real-time audit log of every generation request.
  - Records feature name, prompt version, user inputs, model used, latency in milliseconds, status, and validated JSON output.
  - Zero sensitive credentials or API keys logged.

---

### 8. System Settings (`/settings`)

Configuration, diagnostics, and workspace administration:

- **Google Gemini Connection Diagnostic**:
  - Live connection verification test returning latency and status.
  - Safe key updating: updates active backend session without revealing key in the browser.
  - Model selector (`gemini-2.5-flash` vs `gemini-2.5-pro`).
- **Data Management**:
  - One-click "Reset to NovaTech Demo Data" restoring the canonical evaluation dataset.
- **Architecture Disclosures**:
  - Transparent documentation of technology stack, human-in-the-loop safeguards, and system constraints.

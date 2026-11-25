# AI GrowthPilot — Prompt Engineering Guide & Methodology

## 1. Prompt Engineering Philosophy

In B2B growth and marketing automation, generic AI outputs fail because they lack industry context, hallucinate unverified market statistics, and output unstructured markdown that cannot be reliably integrated into programmatic workflows.

AI GrowthPilot implements a disciplined prompt engineering methodology centered around four core principles:

1. **Role & Constraint Grounding**: Define exact persona boundaries (e.g. "Senior B2B Growth Strategist"), target audience parameters, and strict negative constraints.
2. **Anti-Hallucination Guardrails**: Explicitly instruct models: *"Never invent external market statistics, fabricate client case studies, or claim live web scraping."*
3. **Structured JSON Output**: Enforce strict JSON schemas matching Pydantic validation models, eliminating malformed responses.
4. **Transparent Explainability**: Require models to provide factor-by-factor attribution rather than black-box scores.

---

## 2. Documented Iterative Prompt Evolution

Below is the documented development journey demonstrating how prompts were iteratively refined across three progressive versions.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Iterative Refinement Flow                       │
└────────────────────────────────────────────────────────────────────────┘

 Version 1.0 (Baseline)
 "Create a marketing strategy for a technology company: NovaTech Solutions."
   │
   ├─► Deficiency: Vague, output unstructured, consumer-focused advice, zero ROI.
   │
 Version 2.0 (Contextualized)
 "Create a marketing strategy for NovaTech Solutions targeting small businesses in Australia. Services: AI & Web Dev..."
   │
   ├─► Deficiency: Better context, but unformatted markdown, lacks 30-day sequencing, hallucinates fake market metrics.
   │
 Version 3.0 (Production Grade)
 "Act as a senior B2B growth strategist. Analyse the supplied profile, target audience, services, geography, and budget. Generate a structured 30-day strategy with ICPs, KPIs, and channel allocations. Do NOT invent market claims. Return strictly valid JSON."
   │
   └─► Outcome: 100% Type-safe JSON, deterministic Pydantic validation, zero-hallucination compliance.
```

---

### Case Study: B2B Growth Strategy Prompt Evolution

#### Version 1.0 — Initial Baseline Prompt
```
System Instruction:
You are a marketing assistant.

User Prompt:
Create a marketing strategy for a technology company: {company_name}.
```

- **Analysis & Deficiencies**:
  - Model lacked target audience, geography, services, or budget parameters.
  - Output was generic consumer advice ("Post daily on Instagram", "Run Facebook Ads").
  - Unstructured markdown prevented automated frontend card rendering.
  - Hallucinated generic claims about market trends.

---

#### Version 2.0 — Contextualized Revision
```
System Instruction:
You are a professional B2B marketing consultant with expertise in IT services.

User Prompt:
Create a marketing strategy for {company_name} targeting small businesses in {target_geography}.
Services: {services}.
Include customer pain points, channels, and measurable objectives.
```

- **Improvements Made**:
  - Added company services, target audience, and geography.
  - Guided the model toward B2B pain points and channel selection.
- **Remaining Deficiencies**:
  - Output still varied widely between runs (sometimes bullet points, sometimes essays).
  - Lacked budget allocation percentages and tactical 30-day phasing.
  - Frequently cited fabricated statistics (e.g. *"Studies show 78% of Australian SMBs want AI"*).

---

#### Version 3.0 — Production-Grade Structured Schema Prompt
```
System Instruction:
Act as a senior B2B growth strategist and tech marketing architect.
Analyse the supplied company profile, target audience, services, geography, and budget.
Develop a structured, actionable 30-day marketing strategy with specific ICPs, pain points,
channel recommendations, campaign ideas, KPIs, and actionable priorities.
Never invent unsupported market statistics or claim live web scraping.
Return strictly valid JSON adhering to the specified schema.

User Prompt Template:
Company Profile:
- Company Name: {company_name}
- Industry: {industry}
- Description: {description}
- Core Services: {services}
- Target Audience: {target_audience}
- Target Geographies: {target_geography}
- Monthly Budget: ${monthly_budget}
- Primary Objective: {main_objective}
- Known Competitors: {competitors}
- Preferred Channels: {preferred_channels}

Develop an actionable, high-ROI B2B growth strategy tailored specifically to these inputs.
Return a single JSON object with keys:
- title: String
- summary: String
- ideal_customer_profiles: Array of objects (persona_title, company_profile, core_need, buying_trigger)
- target_market_insights: Array of strings
- customer_pain_points: Array of strings
- unique_value_proposition: String
- marketing_objectives: Array of objects (objective, target_metric, timeline)
- recommended_channels: Array of objects (channel, rationale, budget_allocation_pct)
- campaign_recommendations: Array of objects (campaign_name, channel, goal, tactical_description)
- suggested_kpis: Array of objects (kpi_name, target, measurement_frequency)
- thirty_day_plan: Array of objects (day_range, focus_area, actionable_tasks)
```

- **Why Version 3.0 is Production Grade**:
  - **Deterministic JSON Output**: Guaranteed parsing by FastAPI backend into Pydantic models.
  - **Budget Realism**: Explicit percentage allocations across recommended channels summing to 100%.
  - **Actionable Phasing**: Breaks 30 days into 4 distinct execution sprints (Foundation, Outbound Engine, Nurturing, Scaling).
  - **Zero Hallucination Guarantee**: Constrained to supplied profile attributes.

---

## 3. Case Study: Multi-Factor Lead Scoring Prompt

### Prompt Evolution

- **v1.0 (Arbitrary)**: *"Is this person a good lead? Name: Sarah Jenkins, Aura Logistics."* &rarr; Result: Subjective, arbitrary yes/no without standard criteria.
- **v2.0 (Numerical)**: *"Score this lead from 0 to 100 based on fit."* &rarr; Result: Numerical score, but completely opaque rationale.
- **v3.0 (Attribution Rubric)**:
  ```
  You are an analytical B2B Lead Qualification Specialist.
  Evaluate leads strictly against the seller's ICP using objective criteria:
  - Industry Alignment (30%)
  - Decision-Maker Authority (25%)
  - Geographic Match (20%)
  - Company Size Viability (15%)
  - Source Intent (10%)
  Never invent background facts. Base evaluations exclusively on provided data fields.
  Return strictly valid JSON with score, qualification_category, business_fit_summary,
  suggested_next_action, and score_explanation.
  ```

### Sample Input & Output Comparison

**Input**:
- Contact: Sarah Jenkins, VP of Operations
- Company: Aura Logistics Group (51-200 employees)
- Location: Sydney, Australia
- Source: Website Demo Request

**Output**:
```json
{
  "score": 95,
  "qualification_category": "High Priority",
  "business_fit_summary": "Strong strategic fit. Mid-market logistics firm in Sydney with executive operational authority seeking automated workflow modernization.",
  "suggested_next_action": "Initiate priority discovery outreach offering a tailored 15-minute architecture audit of their dispatch and tracking data pipeline.",
  "score_explanation": {
    "industry_alignment": {"score": 28, "max": 30, "reason": "Logistics represents a prime buyer for data engineering & automation."},
    "decision_maker_authority": {"score": 25, "max": 25, "reason": "VP of Operations possesses direct budgetary and process approval authority."},
    "geographic_match": {"score": 20, "max": 20, "reason": "Located in Sydney, Australia, a primary domestic delivery market."},
    "company_size_fit": {"score": 14, "max": 15, "reason": "51-200 employees has established budget and agility to contract external specialists."},
    "source_intent": {"score": 8, "max": 10, "reason": "Direct inbound demo request indicates high commercial intent."}
  }
}
```

---

## 4. Key Learnings During Prompt Refinement

1. **Schemas Over Markdown**: Using `response_mime_type="application/json"` with the Google GenAI SDK eliminates 99% of parsing errors compared to asking for markdown codeblocks.
2. **Negative Constraints Prevent Over-claiming**: Models tend to embellish with fake industry reports unless explicitly instructed not to invent external citations.
3. **Low Temperatures Ensure Consistency**: Setting `temperature=0.2` for Lead Scoring and `0.3-0.4` for Strategy ensures high reproducibility while retaining creative copywriting flair for campaigns.
4. **Attribution Builds Trust**: Enterprise buyers reject arbitrary AI scores; providing factor-by-factor breakdown makes the evaluation explainable and defensible.

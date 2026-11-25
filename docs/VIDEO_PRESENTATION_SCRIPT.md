# AI GrowthPilot — Video Presentation Script (3–4 Minutes)

**Target Duration:** 3 minutes 45 seconds  
**Speaker Role:** AI Growth & Automation Associate Candidate (Gokul Infocare Technical Assessment)  
**Demonstration Mode:** Live Web Application Running Locally (`http://127.0.0.1:5173`)  
**Application Architecture:** React 19 + TypeScript + Vite | FastAPI + SQLAlchemy + SQLite | Google Gemini 2.5 Flash  

---

## Script & Action Timeline

### 1. Business Problem [0:00 – 0:25] (Duration: 25s)
**Visual Screen:** Title slide & camera view, then transition to browser dashboard (`http://127.0.0.1:5173/`).

> *"Hello, everyone. Small B2B technology agencies and software consultancies face four critical growth bottlenecks:*
> 1. *Their marketing operations are fragmented across disconnected spreadsheets, docs, and ad tools.*
> 2. *Standard generative AI prompts return generic consumer advice with zero enterprise relevance.*
> 3. *Sales teams spend hours pursuing unqualified leads without an objective way to evaluate fit.*
> 4. *And unvetted automation risks brand reputation by publishing hallucinated claims without human review.*
>
> *Today, I'm presenting **AI GrowthPilot** &mdash; an AI-powered growth and marketing automation platform built specifically to solve these problems."*

---

### 2. Project Introduction [0:25 – 0:45] (Duration: 20s)
**Visual Screen:** Overview Dashboard (`/`). Cursor moves across the 5 top summary cards (Total Leads, Qualified Leads, Active Campaigns, Content Scheduled, Average Lead Score) and the Recharts dual-area chart.

> *"AI GrowthPilot unites strategy formulation, multi-channel copywriting, content scheduling, and explainable lead qualification into one centralized command center.*
>
> *For our demonstration, we use **NovaTech Solutions** &mdash; a consultancy delivering custom AI development, modern web engineering, and workflow automation across Australia, the US, and India. Notice that all seeded demonstration records are clearly labeled with a persistent demo badge."*

---

### 3. AI Tools Used [0:45 – 1:05] (Duration: 20s)
**Visual Screen:** Navigate to Settings (`/settings`), showing the AI Configuration panel with `gemini-2.5-flash` model badge and masked credential diagnostics.

> *"Under the hood, we integrate directly with the **Google Gemini API** using the official `google-genai` Python SDK.*
>
> *We keep API keys strictly on the backend in session memory &mdash; keys are never exposed in browser bundles, responses, or client storage. Crucially, we enforce **structured JSON output schemas** validated by Pydantic models, eliminating markdown parsing failures."*

---

### 4. Prompt Engineering & Iterative Improvement [1:05 – 1:30] (Duration: 25s)
**Visual Screen:** Navigate to Prompt Engineering Lab (`/prompt-lab`). Scroll through the side-by-side comparison of Version 1.0, Version 2.0, and Version 3.0.

> *"Prompt engineering is where the real business leverage happens. In our **Prompt Lab**, we have documented our iterative evolution across three versions:*
> - *Our **v1.0 baseline** prompt was vague: 'Create a marketing strategy for a tech company.' It produced generic advice like 'post on Instagram'.*
> - *In **v2.0**, we added business context: geography, services, and buyer pain points.*
> - *Finally, in **v3.0 Production**, we instituted strict persona grounding, explicit anti-hallucination guardrails, and deterministic JSON schemas. We explicitly instruct the model: 'Never invent unsupported market statistics or claim live web scraping.' This guarantees grounded, actionable 30-day playbooks."*

---

### 5. Live AI Generation [1:30 – 1:55] (Duration: 25s)
**Visual Screen:** Navigate to AI Strategy (`/strategy`). Click the "Generate Growth Strategy" button. Watch the loading spinner, then review the synthesized 10-part playbook.

> *"Let's generate a growth strategy. On the **AI Strategy** page, we review NovaTech's profile and click 'Generate Growth Strategy'.*
>
> *Within seconds, the engine delivers a complete 10-part playbook: ideal customer personas with explicit buying triggers, unique value proposition, percentage-based channel budget allocations, and a phased 30-day execution roadmap.*
>
> *Notice our visual source badges &mdash; clearly distinguishing `Gemini AI` from `Demo Simulation` &mdash; as well as our Model Assumptions and Uncertainty Disclosure card."*

---

### 6. Campaign Creation [1:55 – 2:20] (Duration: 25s)
**Visual Screen:** Navigate to Campaign Studio (`/campaigns`). Select LinkedIn as channel, enter objective "Generate 20 qualified discovery calls", and click "Generate Campaign Package".

> *"Moving to **Campaign Studio**, we select LinkedIn and click 'Generate Campaign Package'.*
>
> *The AI crafts a channel-native campaign package: a strategic narrative thesis, three distinct headlines &mdash; benefit-driven, curiosity-driven, and direct commercial &mdash; and three multi-angle content variations: Problem-Agitate-Solve, ROI Transformation, and Contrarian Thought Leadership, complete with one-click clipboard copy and recommended schedules.*
>
> *Every variation can be edited inline and saved directly back to our database."*

---

### 7. Lead Import and Scoring [2:20 – 2:50] (Duration: 30s)
**Visual Screen:** Navigate to Lead Intelligence (`/leads`). Click "Import CSV", drag in `sample_leads.csv`. Open the slide-over detail drawer for "Sarah Jenkins" and click "Re-score AI".

> *"Next, in **Lead Intelligence**, we import a CSV list of prospective clients. The system automatically maps synonym headers, validates email formats, rejects duplicates, and applies our **Explainable 5-Factor Scoring Rubric** (0–100):*
> - *Industry Alignment (30%)*
> - *Decision-Maker Authority (25%)*
> - *Geographic Match (20%)*
> - *Company Size (15%)*
> - *Source Intent (10%)*
>
> *Opening Sarah Jenkins, VP of Operations in Sydney, she scores 95/100. We see the transparent factor breakdown and a concrete next action. We can add internal CRM notes, update pipeline stages, and export sanitized CSVs protected against formula injection (CWE-1236)."*

---

### 8. Technical Architecture [2:50 – 3:10] (Duration: 20s)
**Visual Screen:** Switch to Content Calendar (`/calendar`) and Growth Analytics (`/analytics`).

> *"Our technical architecture follows modern software engineering best practices:*
> - *Frontend: **React 19**, **TypeScript**, **Vite**, **Tailwind CSS**, and **TanStack Query**, optimized with route-level code splitting down to 303 kB.*
> - *Backend: **FastAPI**, **Pydantic v2**, and **SQLAlchemy** with **SQLite**.*
> - *Human-in-the-Loop Governance: Our Content Calendar enforces explicit approval (`Draft` &rarr; `Approved` &rarr; `Published`) before anything is deployed.*
> - *All analytics metrics are dynamically aggregated from real database records."*

---

### 9. Challenges and Solutions [3:10 – 3:30] (Duration: 20s)
**Visual Screen:** Navigate to Settings (`/settings`). Show the clean diagnostics and demo toggle.

> *"A critical engineering challenge was error handling and preventing deceptive AI behavior. Many demos silently convert API failures into fake mock successes.*
>
> *In AI GrowthPilot, we explicitly decoupled three states: `Live Gemini AI`, `Demo Simulation`, and `AI Error`. If Gemini fails due to an invalid key or network timeout, the backend returns HTTP 502 and the UI presents an honest recovery banner giving the user the choice to generate via demo simulation.*
>
> *We also hardened CSV exports against formula injection, capped file uploads at 5MB, and ensured demo resets strictly preserve user-imported leads."*

---

### 10. Final Outcome [3:30 – 3:45] (Duration: 15s)
**Visual Screen:** Return to Overview Dashboard (`/`). Camera on presenter.

> *"In conclusion, AI GrowthPilot is not a static mockup or a fragile wrapper &mdash; it is a full-stack, verified, production-quality SaaS platform backed by 17 automated tests and genuine prompt engineering rigor.*
>
> *It demonstrates how practical generative AI can solve real revenue and automation challenges for technology businesses.*
>
> *Thank you for your time, and I look forward to your questions!"*

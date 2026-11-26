# AI GrowthPilot — Final Assessment Submission Email Draft

**Destination:** `jobs@gokulinfocare.com`  
**Subject:** Application & Technical Assessment Submission: AI Growth & Automation Associate — Dhruv — AI GrowthPilot  
**Candidate Name:** Dhruv  
**Position:** AI Growth & Automation Associate (Work From Home)  
**Company:** Gokul Infocare  
**Submission Date:** November 26, 2026  

---

Dear Gokul Infocare Assessment & Recruitment Team,

I am pleased to submit my completed technical assessment for the **AI Growth & Automation Associate** position.

As requested in Task 1 (AI Skills & Prompt Engineering Assessment), I have designed, engineered, tested, and packaged **AI GrowthPilot** — an enterprise-grade business growth and marketing automation SaaS platform built specifically for small technology companies, software agencies, and AI consultancies.

---

### Key Project Links & Deliverables

* **DELIVERABLE A — Video Presentation (3:45 Walkthrough):**  
  [Link to Video Presentation / `submission/AI_GrowthPilot_Assessment_Demo.mp4`]  
  *(A complete timestamped presentation script with exact UI actions and talking points is also available in the repository at [`docs/VIDEO_PRESENTATION_SCRIPT.md`](https://github.com/Dhruv17204/ai-growthpilot/blob/main/docs/VIDEO_PRESENTATION_SCRIPT.md).)*

* **DELIVERABLE B — Development Prompt Journal:**  
  [https://github.com/Dhruv17204/ai-growthpilot/blob/main/docs/DEVELOPMENT_PROMPT_JOURNAL.md](https://github.com/Dhruv17204/ai-growthpilot/blob/main/docs/DEVELOPMENT_PROMPT_JOURNAL.md)  
  *(Detailed chronicle of the actual iterative prompts, AI tools, revisions, challenges, and validation steps across 12 development stages.)*

* **DELIVERABLE C — Public GitHub Repository:**  
  [https://github.com/Dhruv17204/ai-growthpilot](https://github.com/Dhruv17204/ai-growthpilot)  
  *(Includes comprehensive quick-start guides, single-container Docker deployment instructions, full test suite documentation, and architectural specifications.)*

---

### Project Overview: AI GrowthPilot

Technology agencies frequently struggle with fragmented marketing operations across disconnected spreadsheets, superficial consumer-level generative AI advice, unvetted lead pipelines, and lack of human approval controls. 

**AI GrowthPilot** unites these workflows into a single full-stack command center across 8 integrated modules:
1. **Overview Dashboard:** Live KPI summaries and database aggregations.
2. **AI Growth Strategy:** 10-part B2B playbooks with ICP buying triggers, budget allocations, and uncertainty disclosures.
3. **Campaign Studio:** Multi-angle channel copywriting (PAS, ROI Transformation, Contrarian Thought Leadership) with inline editing.
4. **Content Calendar:** 7-day editorial scheduling with human-in-the-loop lifecycle states (`Draft` → `Pending Approval` → `Approved` → `Published`).
5. **Lead Intelligence:** CSV import with synonym mapping, duplicate detection, CWE-1236 formula injection defense, and an explainable 5-factor scoring rubric (0–100).
6. **Growth Analytics:** Authentic SQL aggregates for CPL, CTR, and ROI with graceful empty-state handling.
7. **Prompt Engineering Lab:** Interactive benchmark comparison of v1.0, v2.0, and v3.0 prompts with negative constraints and telemetry audit logs.
8. **System Settings:** Non-leaking Gemini API diagnostics, model selection (`gemini-2.5-flash`), and demo data re-seeding.

---

### Technical Highlights & Engineering Rigor

* **Decoupled 3-State AI Engine:** Integrates Google Gemini 2.5 Flash via the official `google-genai` Python SDK. Explicitly separates `LIVE AI`, `DEMO SIMULATION`, and `AI ERROR` states (HTTP 502 with honest recovery prompts) so API failures are never silently disguised as fake mock successes.
* **Full-Stack Architecture:** React 19 + TypeScript + Vite + Tailwind CSS + TanStack Query frontend paired with a Python FastAPI + SQLAlchemy 2.0 + SQLite backend. Route-level code-splitting reduces the main application bundle to 303.8 kB.
* **Defensive Security Engineering:** In-memory sliding-window rate limiter with atomic in-flight slot reservation, session-bound double-submit CSRF protection, server-side session revocation, and sanitized CSV exports.
* **Automated Verification:** **76 automated tests** (73 backend Pytest tests, 84.03% backend statement coverage, and 3 frontend Vitest unit tests) passing with a 100% green 3-job GitHub Actions CI pipeline. Single-container multi-stage Docker deployment verified.

---

### Reviewer Quick Start

To run the application locally via Docker:
```bash
git clone https://github.com/Dhruv17204/ai-growthpilot.git
cd ai-growthpilot
docker build -t ai-growthpilot .
docker run -p 8000:8000 ai-growthpilot
```
Then visit `http://127.0.0.1:8000` in your browser. (Alternatively, standard local `npm run dev` and `uvicorn` setup instructions are detailed in the `README.md`.)

---

Thank you for the opportunity to participate in this technical assessment. I look forward to your review and feedback, and I would welcome the opportunity to discuss how I can contribute to Gokul Infocare as an AI Growth & Automation Associate.

Sincerely,  
**Dhruv**  
Candidate for AI Growth & Automation Associate  
Repository: [https://github.com/Dhruv17204/ai-growthpilot](https://github.com/Dhruv17204/ai-growthpilot)

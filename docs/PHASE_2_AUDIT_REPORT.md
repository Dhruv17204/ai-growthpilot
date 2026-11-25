# AI GrowthPilot — Phase 2 Production-Quality Audit Report

**Date:** November 25, 2026  
**Auditor:** Senior Software Architect, Application Security Auditor & AI QA Engineer  
**Project Path:** `C:\Users\dhruv\.gemini\antigravity\scratch\ai-growthpilot`  
**Assessment Standards:** Correctness, Reliability, Security, Explainability, Assessment Readiness  

---

## 1. Executive Summary

A comprehensive, line-by-line audit of the AI GrowthPilot codebase was executed across all frontend pages, backend services, database models, Gemini API integrations, CSV processing pipelines, security boundaries, and test suites.

The core architecture (React 19 + TypeScript + FastAPI + SQLAlchemy + Google GenAI SDK) is robust and functional. However, the audit uncovered **several high-priority defects and security risks**—most notably:
1. **Silent Fallback Conversion:** Failed Gemini requests when an API key was configured were caught and silently converted into successful-looking demo responses, falsely claiming AI completion.
2. **CSV Formula Injection:** The lead export endpoint directly serialized raw user inputs without sanitizing formula trigger characters (`=`, `+`, `-`, `@`).
3. **Destructive Reset Demo Data:** The demo reset function executed an unqualified delete on the `leads` table, destroying user-imported data.
4. **Uncalibrated Lead Scoring Rubric:** Maximum point allocations capped total scores at 95/100 rather than the documented 100/100 scale.
5. **Monolithic Bundle Size:** Lack of route-level code splitting resulted in an 880 KB main bundle.

Each verified defect, its impact, and recommended remediation are detailed below.

---

## 2. Verified Issues & Defects Catalog

### Defect 1: Silent Conversion of AI API Errors into Fallback Responses
- **Location:**
  - `backend/app/services/ai_strategy_service.py` (Lines 264–275)
  - `backend/app/services/campaign_service.py` (Lines 148–159)
  - `backend/app/services/content_service.py` (Lines 200–215)
  - `backend/app/services/lead_scoring_service.py` (Lines 200–210)
  - `frontend/src/pages/StrategyPage.tsx` (Line 66)
- **Severity:** **CRITICAL**
- **Problem Description:**  
  When a Gemini API key is configured and an API call fails (due to an invalid key, quota exhaustion, network timeout, or content safety filter), `gemini_client.generate_structured_json` returns `status="error"`. However, the calling services immediately caught this and executed `generate_fallback_*()`, replaced the payload, saved it to the database, and returned HTTP 200. On the frontend, `StrategyPage.tsx` unconditionally alerted: *"Growth Strategy successfully generated using Gemini AI!"*.
- **Why It Matters:**  
  Directly violates assessment integrity and user transparency. A failed AI call was deceptively presented as a successful Gemini generation, masking API errors.
- **Recommended Correction:**  
  Strictly decouple the 3 execution states:
  1. `LIVE AI`: Genuine Gemini success (`status: "success"`, `is_demo: false`).
  2. `DEMO MODE`: Explicit simulation (`status: "fallback_demo"`, `is_demo: true`).
  3. `AI ERROR`: Genuine Gemini failure (`status: "error"`, `error_message: "..."`).
  If an API key is configured and fails, return HTTP 502 with the exact error message and an explicit UI prompt offering: *"Retry with Gemini"* or *"Generate in Demo Mode Instead"*. Never save failed runs as valid AI completions.

---

### Defect 2: Missing Visual Source Indicators on Generated Artifacts
- **Location:**  
  `frontend/src/pages/StrategyPage.tsx`, `CampaignStudioPage.tsx`, `ContentCalendarPage.tsx`, `LeadIntelligencePage.tsx`
- **Severity:** **HIGH**
- **Problem Description:**  
  Generated strategy cards, campaign variations, calendar items, and lead score cards lacked prominent visual badges indicating whether the content originated from **Gemini AI** or **Demo Simulation**.
- **Why It Matters:**  
  Users and evaluators cannot distinguish between live generative AI completions and local deterministic simulation playbooks.
- **Recommended Correction:**  
  Render a permanent source pill on every generated item:
  - `Gemini AI` (Emerald badge with Sparkles icon) when `is_demo === false`.
  - `Demo Simulation` (Violet/Amber badge with Info icon) when `is_demo === true`.

---

### Defect 3: CSV Formula Injection Vulnerability in Lead Export
- **Location:**  
  `backend/app/routers/leads_router.py` (Lines 68–91)
- **Severity:** **HIGH (SECURITY)**
- **Problem Description:**  
  The `/api/leads/export` endpoint streamed CSV cells (`l.name`, `l.company`, `l.job_title`, etc.) directly into a `csv.writer` without sanitization. If an uploaded lead contains formula syntax (e.g. `=cmd|'/C calc'!A0`, `@SUM(...)`, `+`, `-`), opening the exported CSV in Microsoft Excel or Google Sheets triggers DDE code execution or data exfiltration.
- **Why It Matters:**  
  Common high-severity vulnerability (CWE-1236: Improper Neutralization of Formula Elements in CSV File).
- **Recommended Correction:**  
  Sanitize every exported cell string: if a string starts with `=`, `+`, `-`, `@`, `\t`, or `\r`, prepend a single quote `'` or tab escape to neutralize formula interpretation.

---

### Defect 4: Destructive Demo Reset Wiping User Data
- **Location:**  
  `backend/app/services/seed_data_service.py` (Lines 24–35)
- **Severity:** **HIGH**
- **Problem Description:**  
  The `seed_database(db, force_reset=True)` function invoked `db.query(Lead).delete()` and `db.query(Campaign).delete()` without filtering for `is_demo == True`.
- **Why It Matters:**  
  If a user uploads their own proprietary leads or creates custom campaigns and later clicks *"Reset to NovaTech Demo Data"*, all user-imported leads were permanently destroyed.
- **Recommended Correction:**  
  Restrict reset deletions strictly to demo records: `db.query(Lead).filter(Lead.is_demo == True).delete()`, preserving user-imported leads (`is_demo == False`).

---

### Defect 5: Uncalibrated Lead Scoring Weights (Max Score Capped at 95)
- **Location:**  
  `backend/app/services/lead_scoring_service.py` (Lines 70–135)
- **Severity:** **MEDIUM**
- **Problem Description:**  
  The documented rubric specifies: Industry (30%), Authority (25%), Geography (20%), Company Size (15%), Source Intent (10%), summing to 100%. However, the top conditional branches allocated:
  - Industry: max 28 (instead of 30)
  - Authority: max 24 (instead of 25)
  - Geography: max 19 (instead of 20)
  - Company Size: max 14 (instead of 15)
  - Source Intent: max 10
  Sum of maximum possible points was: `28 + 24 + 19 + 14 + 10 = 95`. A 100% ideal prospect could never achieve a score above 95.
- **Why It Matters:**  
  Creates mathematical inconsistency between documented specifications and actual calculation logic.
- **Recommended Correction:**  
  Recalibrate point boundaries so exact ICP matches receive full marks (30, 25, 20, 15, 10), and enforce `max(0, min(100, score))`.

---

### Defect 6: CSV Upload Validation Gaps (Missing Size Cap & Permissive Email Regex)
- **Location:**  
  `backend/app/routers/leads_router.py` (Lines 15–25)
  `backend/app/services/lead_scoring_service.py` (Lines 345–355)
- **Severity:** **MEDIUM**
- **Problem Description:**  
  - No file size validation before reading `await file.read()`. A massive file (e.g. 100MB) could cause excessive memory consumption or denial of service.
  - File extension check used `file.filename.endswith(".csv")`, which fails on uppercase `.CSV` or missing filenames.
  - Email validation only checked `"@" in email`, accepting invalid values like `"user@"`, `"@domain"`, or `"user@domain"`.
- **Why It Matters:**  
  Leads to corrupted database records and crashes on unexpected CSV formats.
- **Recommended Correction:**  
  - Enforce a 5MB maximum file size check.
  - Case-insensitive extension check (`filename.lower().endswith(".csv")`).
  - Standard RFC-compliant email regex (`^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$`).

---

### Defect 7: Relative SQLite Database Path Dependency
- **Location:**  
  `backend/app/config.py` (Line 10)
- **Severity:** **MEDIUM**
- **Problem Description:**  
  `DATABASE_URL: str = "sqlite:///./growthpilot.db"` relies on the process working directory. Starting uvicorn from the project root creates `growthpilot.db` in `ai-growthpilot/`, while starting from `backend/` creates it in `backend/`.
- **Why It Matters:**  
  Can lead to split database states where seeded data or tests appear missing depending on which directory the shell was in.
- **Recommended Correction:**  
  Calculate an absolute base path anchored to `backend/growthpilot.db`.

---

### Defect 8: Monolithic Frontend Bundle (880 KB) Due to Missing Route Code-Splitting
- **Location:**  
  `frontend/src/App.tsx` (Lines 3–12)
  `frontend/vite.config.ts`
- **Severity:** **MEDIUM (PERFORMANCE)**
- **Problem Description:**  
  All 8 module pages (`OverviewPage`, `StrategyPage`, `CampaignStudioPage`, etc.) and the entire Recharts library were statically imported in `App.tsx`, creating an 880 KB monolithic JavaScript bundle.
- **Why It Matters:**  
  Increases initial page load time and bandwidth usage.
- **Recommended Correction:**  
  Implement `React.lazy()` route-level code splitting with a `<Suspense>` boundary and configure `manualChunks` in `vite.config.ts` to separate vendor dependencies (`recharts`, `lucide-react`).

---

### Defect 9: Synchronous Gemini SDK Call in Async Endpoint
- **Location:**  
  `backend/app/services/gemini_client.py` (Line 111)
- **Severity:** **LOW / MEDIUM**
- **Problem Description:**  
  `self._client.models.generate_content` is synchronous. Calling it inside `async def generate_structured_json` blocks FastAPI's event loop during network roundtrips.
- **Why It Matters:**  
  Degrades backend concurrency for concurrent requests.
- **Recommended Correction:**  
  Wrap the synchronous call with `asyncio.to_thread` or utilize `asyncio.wait_for(..., timeout=45.0)`.

---

### Defect 10: Anti-Hallucination & Uncertainty Prompting Gaps
- **Location:**  
  `backend/app/services/prompt_service.py` (Prompt templates)
- **Severity:** **LOW**
- **Problem Description:**  
  Prompts contained negative constraints ("do not invent statistics") but lacked positive guidance instructing the model to explicitly declare assumptions when business profile data is incomplete.
- **Why It Matters:**  
  Leads to unwarranted overconfidence in generated strategies when minimal inputs are provided.
- **Recommended Correction:**  
  Instruct models to flag any assumed data under an explicit `"assumptions_and_uncertainties"` section.

---

## 3. Audit Verification Matrix

| Area | Component | Audit Status | Key Action Required |
| :--- | :--- | :--- | :--- |
| **AI Integration** | `gemini_client.py` | Defective Error State | Decouple 3 states; prevent silent fallback conversion |
| **AI Strategy** | `ai_strategy_service.py` | Masked Errors | Surface genuine errors; offer explicit demo toggle |
| **Campaigns** | `campaign_service.py` | Masked Errors | Add visible source badge & explicit error recovery |
| **Content** | `content_service.py` | Masked Errors | Add source badge & workflow approval enforcement |
| **Lead Scoring** | `lead_scoring_service.py` | Weight Discrepancy | Recalibrate weights (30/25/20/15/10) to reach 100 |
| **CSV Export** | `leads_router.py` | Vulnerability | Sanitize formula characters (`=`, `+`, `-`, `@`) |
| **Database** | `config.py` & `seed_data_service.py` | Path / Data Loss | Anchor DB path; preserve user data on demo reset |
| **Frontend** | `App.tsx` & Pages | Monolithic / No Badges | Implement route-lazy loading & source pill badges |
| **Security** | `.gitignore` | Missing Ignores | Ensure `growthpilot.db`, `.env`, `venv` are ignored |
| **Testing** | `test_api.py` | Missing Failure Tests | Add tests for missing keys, error states & CSV injection |

---

## 4. Next Steps

Execution will proceed immediately to **Phase 2 (Gemini Integration & 3-State Decoupling)** and subsequent remediation phases.

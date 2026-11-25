# AI GrowthPilot — GitHub Publication & Verification Report

**Date of Publication:** November 25, 2026  
**Candidate Role:** AI Growth & Automation Associate (Technical Portfolio Assessment)  
**Target Organization:** Gokul Infocare  
**GitHub Account:** [Dhruv17204](https://github.com/Dhruv17204)  
**Published Repository:** [`https://github.com/Dhruv17204/ai-growthpilot`](https://github.com/Dhruv17204/ai-growthpilot)  
**Publication Status:** **LIVE & PUBLICLY ACCESSIBLE**  

---

## 1. Environment & Tooling Installation Status

- **Git Installation:** Standalone official Git engine (MinGit v2.56.1.windows.1) installed in `$env:LOCALAPPDATA\Programs\Git\cmd` and permanently configured in user PATH.
- **GitHub CLI (`gh`):** GitHub CLI v2.102.0 located at `C:\Program Files\GitHub CLI\gh.exe`.
- **PowerShell Execution:** Unrestricted script execution for virtual environment activation and automation.

---

## 2. Authenticated GitHub Identity

- **Command:** `gh api user --jq .login`
- **Authenticated Username:** `Dhruv17204`
- **User ID:** `218955594`
- **Commit Author:** `Dhruv17204 <218955594+Dhruv17204@users.noreply.github.com>`
- **Token Privacy:** GitHub token preserved securely in Windows keyring; zero token leakage in logs or commits.

---

## 3. Security Checks Performed

| Security Dimension | Verification Method | Result |
| :--- | :--- | :---: |
| **API Secret Scan** | Regex search for Google API keys, JWTs, and private keys | **0 SECRETS FOUND** |
| **CWE-1236 Formula Defense** | CSV cell single-quote prefixing (`'`, `=`, `+`, `-`, `@`) | **PASSED & VERIFIED** |
| **Upload Guardrails** | 5 MB upload size enforcement and MIME-type validation | **PASSED & VERIFIED** |
| **Credential Exclusion** | `.gitignore` rule verification for `.env*` and `*.key` | **PASSED & VERIFIED** |
| **Database Isolation** | Exclusion of binary SQLite databases (`growthpilot.db`) | **PASSED & VERIFIED** |
| **Session API Keys** | API keys accepted only via backend memory / session | **PASSED & VERIFIED** |

---

## 4. Files Included & Excluded

### Included (78 Release Files Staged & Published):
- **Root:** `.env.example`, `.gitignore`, `README.md`, `sample_leads.csv`
- **Documentation (`docs/`):** 14 markdown documents + 8 high-resolution product screenshots (`docs/screenshots/01_overview_dashboard.png` through `08_system_settings.png`)
- **Backend (`backend/`):** 23 files including FastAPI routers, Pydantic schemas, SQLAlchemy models, Gemini integration client, lead scoring rubric, seed data service, and 17 Pytest unit/integration tests
- **Frontend (`frontend/`):** 28 files including React 19 pages, Lucide icons, Tailwind configuration, TanStack Query API hooks, Recharts dashboard visualizations, and Vite configuration

### Excluded (Blocked by `.gitignore` & Cleaned):
- `.env`, `.env.local` (zero credentials committed)
- `backend/growthpilot.db`, `backend/test_growthpilot.db` (local SQLite databases)
- `backend/venv/`, `backend/.pytest_cache/`, `backend/**/__pycache__/`
- `frontend/node_modules/`, `frontend/dist/`, `frontend/tsconfig.tsbuildinfo`

---

## 5. Repository Details & Remote Configuration

- **Repository Name:** `ai-growthpilot`
- **Repository URL:** [`https://github.com/Dhruv17204/ai-growthpilot`](https://github.com/Dhruv17204/ai-growthpilot)
- **Git Remote (Fetch & Push):** `https://github.com/Dhruv17204/ai-growthpilot.git`
- **Visibility:** **PUBLIC**
- **Default Branch:** `main`

---

## 6. Commit Verification

- **Commit Message:** `feat: initial release of AI GrowthPilot platform`
- **Commit SHA:** `819cc0fbc01e32b4336eabe671c5c41126486b2d` (Short: `819cc0f`)
- **Remote Push Result:**
  ```
  To https://github.com/Dhruv17204/ai-growthpilot.git
   * [new branch]      HEAD -> main
  branch 'main' set up to track 'origin/main'.
  ```

---

## 7. Public Accessibility & Asset Verification

Verified live via GitHub API:
1. **Repository Access:** Confirmed `public` via `gh api repos/Dhruv17204/ai-growthpilot`.
2. **README.md Rendering:** Confirmed root `README.md` is active with all badges, architecture diagrams, and quickstart commands.
3. **Screenshots Verified Live on Remote:**
   - `01_overview_dashboard.png` &mdash; Verified present on remote
   - `02_growth_strategy.png` &mdash; Verified present on remote
   - `03_campaign_studio.png` &mdash; Verified present on remote
   - `04_content_calendar.png` &mdash; Verified present on remote
   - `05_lead_intelligence.png` &mdash; Verified present on remote
   - `06_growth_analytics.png` &mdash; Verified present on remote
   - `07_prompt_lab.png` &mdash; Verified present on remote
   - `08_system_settings.png` &mdash; Verified present on remote
4. **Assessment Documentation:** All 14 technical reports and walkthroughs are accessible in `docs/`.

---

## 8. Remaining Limitations & Boundaries

1. **Demonstration Dataset:** Fictional technology firm "NovaTech Solutions" is pre-seeded for portfolio evaluation.
2. **Social Publishing Simulation:** Status `Published` is a workflow tag requiring human oversight; automated cold outreach without human review is intentionally prevented.
3. **Live Gemini Credentials:** Live API generation requires entering a valid `GEMINI_API_KEY` in UI Settings or `.env`. In its absence, the platform operates in 100% verified Demo Simulation mode.

---

> ### ✅ FINAL CONCLUSION
> AI GrowthPilot is successfully published to GitHub under `Dhruv17204/ai-growthpilot`. The repository is publicly accessible, thoroughly tested, securely hardened, and fully ready for final submission to Gokul Infocare.

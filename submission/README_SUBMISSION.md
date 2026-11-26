# AI GrowthPilot — Final Submission Package Guide

**Assessment:** Task 1 — AI Skills & Prompt Engineering Assessment  
**Organization:** Gokul Infocare  
**Role:** AI Growth & Automation Associate — Work From Home  
**Project:** AI GrowthPilot — AI-Powered Business Growth & Marketing Automation Platform  
**Candidate:** Dhruv  
**Date:** 2026-11-26  

---

## Submission Package Inventory

This `submission/` directory contains all final deliverables and submission resources prepared for Gokul Infocare:

```text
submission/
├── README_SUBMISSION.md               # This inventory and submission instruction guide
├── FINAL_SUBMISSION_EMAIL.md          # Formatted, ready-to-send email draft for jobs@gokulinfocare.com
├── FINAL_SUBMISSION_CHECKLIST.md      # Mirror of docs/FINAL_SUBMISSION_CHECKLIST.md
└── AI_GrowthPilot_Assessment_Demo.mp4 # Video recording file destination (or external link)
```

---

## 1. Deliverables Mapping

### Deliverable A — Video Presentation (Min 2 Minutes)
* **Status:** Complete Script & Shot List Prepared  
* **Script Location:** [`docs/VIDEO_PRESENTATION_SCRIPT.md`](../docs/VIDEO_PRESENTATION_SCRIPT.md)  
* **Target Duration:** 3:45  
* **Recommended Next Action:**
  1. Launch the application locally (`docker run -p 8000:8000 ai-growthpilot` or via `npm run dev` + `uvicorn`).
  2. Open OBS Studio or Windows Game Bar (`Win + Alt + R`).
  3. Walk through the 10 timestamped sections in [`docs/VIDEO_PRESENTATION_SCRIPT.md`](../docs/VIDEO_PRESENTATION_SCRIPT.md).
  4. Save the recording to `submission/AI_GrowthPilot_Assessment_Demo.mp4` or upload to Google Drive/YouTube Unlisted and insert the URL in `submission/FINAL_SUBMISSION_EMAIL.md`.

### Deliverable B — Development Prompt Journal
* **Status:** Complete & Committed  
* **Location:** [`docs/DEVELOPMENT_PROMPT_JOURNAL.md`](../docs/DEVELOPMENT_PROMPT_JOURNAL.md)  
* **Summary:** Documents the actual prompts, revisions, AI tools, objectives, challenges, and validations across 12 development phases.

### Deliverable C — Accessible Project Link
* **Status:** Complete & Public  
* **Repository URL:** [https://github.com/Dhruv17204/ai-growthpilot](https://github.com/Dhruv17204/ai-growthpilot)  
* **Instructions:** Detailed in [`README.md`](../README.md) for both local development and Docker containerization.

---

## 2. Reviewer Verification Steps

Reviewers can verify the application in 3 steps:

1. **Clone & Run with Docker:**
   ```bash
   git clone https://github.com/Dhruv17204/ai-growthpilot.git
   cd ai-growthpilot
   docker build -t ai-growthpilot .
   docker run -p 8000:8000 ai-growthpilot
   ```
2. **Access the Web Interface:**
   Navigate to `http://127.0.0.1:8000`.
3. **Run Automated Test Suites:**
   ```bash
   # Backend (73 tests, 84.03% coverage)
   cd backend && .\venv\Scripts\pytest -v --cov=app
   # Frontend (3 tests)
   cd ../frontend && npm test
   ```

---

## 3. Ready to Submit

Once the candidate confirms the video link and merges PR #1 into `main`:
1. Copy the contents of [`submission/FINAL_SUBMISSION_EMAIL.md`](FINAL_SUBMISSION_EMAIL.md).
2. Insert the final video link.
3. Send to `jobs@gokulinfocare.com`.

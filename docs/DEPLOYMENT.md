# AI GrowthPilot — Production Deployment Guide

## 1. Deployment Architecture

AI GrowthPilot can be deployed as two decoupled services (Frontend SPA + Backend API) or as a containerized unified service:

```
┌───────────────────────────────────────┐
│     Cloudflare Pages / Vercel         │ ◄── React 19 Frontend SPA (Static CDN)
└──────────────────┬────────────────────┘
                   │
                   │ HTTPS API calls
                   ▼
┌───────────────────────────────────────┐
│     Render / Railway / Cloud Run      │ ◄── FastAPI Python Backend (Uvicorn)
│  (Persistent Volume for SQLite DB)   │
└───────────────────────────────────────┘
```

---

## 2. Option A: Containerized Deployment (Docker)

### Dockerfile (Backend)
Create `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
cd backend
docker build -t ai-growthpilot-backend .
docker run -p 8000:8000 -e GEMINI_API_KEY="your-api-key" ai-growthpilot-backend
```

---

## 3. Option B: Cloud Hosting (Render / Railway / Vercel)

### Backend on Render / Railway
1. Connect your GitHub repository to **Render** or **Railway**.
2. Set Environment: **Python 3**.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Configure Environment Variables:
   - `GEMINI_API_KEY`: `AIzaSy...` (from Google AI Studio)
   - `GEMINI_MODEL`: `gemini-2.5-flash`
   - `CORS_ORIGINS`: `https://your-frontend.vercel.app`
   - `DATABASE_URL`: `sqlite:///./growthpilot.db` (Attach a persistent disk for database durability across deploys)

### Frontend on Vercel / Netlify
1. Connect repository root with root directory set to `frontend`.
2. Framework Preset: **Vite**.
3. Build Command: `npm run build`
4. Output Directory: `dist`
5. Environment Variables:
   - `VITE_API_BASE`: `https://your-backend.onrender.com/api`

---

## 4. Production Checklist

- [x] Configure production CORS origins to restrict access to trusted frontend domain.
- [x] Ensure `DEMO_MODE=false` in production environment when live Gemini key is set.
- [x] Attach persistent block storage volume if using SQLite in production, or point `DATABASE_URL` to a managed PostgreSQL instance.
- [x] Verify API health endpoint at `/api/health`.
- [x] Execute automated tests prior to deployment pipeline trigger.

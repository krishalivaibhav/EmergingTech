# AI Resume & Job Match Analyzer

A full-stack FastAPI web app that compares a candidate resume against a job description and returns structured ATS-style insights and resume improvement guidance.

## Project Overview

This tool acts like a recruiter + ATS assistant. Users can upload a PDF resume (or paste resume text), add a job description, and generate:

- Match score out of 100
- Matching and missing skills
- Recruiter-style resume summary
- ATS keyword and wording suggestions
- Rewritten, role-tailored bullet points
- Likely interview questions
- Extra `Tailor My Resume` suggestions

## Features

- PDF resume upload support
- Optional manual resume text input
- CV-first scan flow (score, summary, strengths, improvement areas)
- Resume-based role discovery (`current_status` + suggested roles)
- Role selector workflow with optional role-based JD templating
- Large editable job description input
- Free built-in ATS-style analyzer (no API key required)
- Optional OpenAI-powered structured JSON analysis
- Clean, responsive UI with result cards
- Strong input validation and API error handling
- Environment-variable-based API key management
- Dockerized for local/dev deployment

## Tech Stack

- Backend: FastAPI
- Frontend: Jinja templates + vanilla HTML/CSS/JS
- Analysis Engine: Groq API or local free LLM via Ollama + heuristic fallback + optional OpenAI API
- PDF Parsing: `pypdf`
- Deployment: Docker + Uvicorn

## Project Structure

```text
.
├── app
│   ├── main.py
│   ├── models
│   │   └── schemas.py
│   ├── routes
│   │   ├── api.py
│   │   └── web.py
│   ├── services
│   │   ├── analyzer.py
│   │   ├── free_analyzer.py
│   │   ├── groq_service.py
│   │   ├── llm_service.py
│   │   ├── local_llm_service.py
│   │   └── pdf_parser.py
│   ├── static
│   │   ├── css
│   │   │   └── styles.css
│   │   └── js
│   │       └── app.js
│   └── templates
│       └── index.html
├── .dockerignore
├── .env.example
├── Dockerfile
├── README.md
└── requirements.txt
```

## Setup Instructions (Local)

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
cp .env.example .env
```

Then update `.env`:

```env
ANALYZER_MODE=free
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_TIMEOUT_SECONDS=120
```

Mode options:

- `ANALYZER_MODE=local_llm`: use real local LLM via Ollama (free, no API key).
- `ANALYZER_MODE=groq`: use Groq-hosted LLM analysis with `GROQ_API_KEY`.
- `ANALYZER_MODE=auto`: try OpenAI if key is set, then Groq if key is set, then local LLM, then heuristic fallback.
- `ANALYZER_MODE=free`: always use free local analysis (no API key).
- `ANALYZER_MODE=openai`: require OpenAI key and use model-based analysis.

### Run With Groq

1. Add your API key to `.env`:

```env
ANALYZER_MODE=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
OPENAI_API_KEY=
```

2. Run the FastAPI app:

```bash
uvicorn app.main:app --reload
```

This uses Groq as the structured LLM backend and avoids running Ollama locally.

### Run With A Real Free LLM (Ollama)

1. Install Ollama: https://ollama.com/download
2. Start Ollama app/service.
3. Pull a free model:

```bash
ollama pull llama3.1:8b
```

4. Keep `.env` as:

```env
ANALYZER_MODE=local_llm
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OPENAI_API_KEY=
```

5. Run the FastAPI app normally:

```bash
uvicorn app.main:app --reload
```

This gives you actual LLM-generated analysis without paid API usage.

4. Run the app:

```bash
uvicorn app.main:app --reload
```

5. Open in browser:

```text
http://127.0.0.1:8000
```

## Docker Run Instructions

1. Build image:

```bash
docker build -t ai-resume-analyzer .
```

2. Run container:

```bash
docker run --env-file .env -p 8000:8000 ai-resume-analyzer
```

3. Access app:

```text
http://localhost:8000
```

## API Behavior

### `POST /api/scan-cv`

Accepts `multipart/form-data`:

- `resume_file` (optional, PDF only)
- `resume_text` (optional)

At least one of `resume_file` or `resume_text` must be provided.

Response shape:

```json
{
  "cv_score": 74,
  "current_status": "Early Career",
  "profile_summary": "Profile appears early career with strengths around Python...",
  "recommended_roles": ["Backend Engineer", "Software Engineer"],
  "resume_summary": "Candidate shows relevant experience...",
  "top_strengths": ["Python", "REST APIs"],
  "improvement_areas": ["System Design", "Kubernetes"],
  "ats_suggestions": ["Quantify impact with metrics..."],
  "improved_bullets": ["Built backend services..."]
}
```

### `POST /api/analyze`

Accepts `multipart/form-data`:

- `resume_file` (optional, PDF only)
- `resume_text` (optional)
- `job_description` (optional if `target_role` is provided)
- `target_role` (optional role selected from suggested roles)

At least one of `resume_file` or `resume_text` must be provided.
At least one of `job_description` or `target_role` must be provided.

Response shape:

```json
{
  "match_score": 78,
  "matching_skills": ["Python", "FastAPI"],
  "missing_skills": ["Kubernetes"],
  "resume_summary": "Candidate has backend-focused experience...",
  "ats_suggestions": ["Add cloud deployment keywords..."],
  "improved_bullets": ["Built API platform reducing latency by 35%..."],
  "interview_questions": ["How did you scale your API under load?"],
  "tailor_my_resume": {
    "improved_professional_summary": "Backend engineer with...",
    "stronger_project_bullets": ["Led X project..."],
    "suggested_skills_keywords": ["CI/CD", "Docker", "Microservices"]
  }
}
```

### `POST /api/suggest-roles`

Accepts `multipart/form-data`:

- `resume_file` (optional, PDF only)
- `resume_text` (optional)

At least one of `resume_file` or `resume_text` must be provided.

Response shape:

```json
{
  "current_status": "Mid Level",
  "profile_summary": "Profile appears mid level with strengths around Python, SQL...",
  "recommended_roles": [
    "Backend Engineer",
    "Software Engineer",
    "Full Stack Developer"
  ]
}
```

## Prompting Approach

When OpenAI mode is enabled, the app uses a structured internal prompt that instructs the model to behave as an expert ATS evaluator and recruiter, returning strict JSON with actionable recommendations.

In `local_llm` mode, the app sends the structured recruiter prompt to your local Ollama model and parses JSON output.

In `free` mode, the app uses deterministic ATS heuristics (skill overlap, keyword gap analysis, bullet rewrites, and role-targeted suggestions) as a backup path.

## Error Handling Included

- Missing role/JD context (neither job description nor target role provided)
- Missing resume input (no file and no pasted text)
- Invalid file type (non-PDF uploads)
- Empty/unreadable PDF text
- Missing `OPENAI_API_KEY` when `ANALYZER_MODE=openai`
- Upstream LLM failures or malformed responses

## Deployment Notes

- Works on any container platform supporting Docker (Render, Railway, Fly.io, ECS, etc.)
- Set `ANALYZER_MODE=local_llm` for keyless LLM-based deployment when Ollama is available
- In Docker Desktop on macOS/Windows, use `OLLAMA_BASE_URL=http://host.docker.internal:11434`
- If using OpenAI, set `OPENAI_API_KEY` securely in platform secrets
- Use `OPENAI_MODEL` to swap model versions without code changes
- `GET /healthz` endpoint is available for health checks

## Sample Workflow

1. Open the app in browser.
2. Upload a PDF resume or paste resume text.
3. Click **Scan CV** to get CV score, profile summary, and suggested roles.
4. (Optional) Open **Job Match Tools**, pick a role, and paste a specific JD.
5. Click **Analyze Selected Role** for role-targeted matching output.
6. Iterate on resume copy and re-run CV scan/analysis.

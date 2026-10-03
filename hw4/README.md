# Campus Customs (MGT409 Homework 4)

A Yale apparel shop website with **Buddy**, a PydanticAI shopping agent. Shoppers can browse products, create an account, log in, and chat with Buddy, who looks up real prices and stock in the database and puts matching products on the page.

- **Front end:** React + Vite + TypeScript (`frontend/`)
- **Back end:** FastAPI + PydanticAI (`backend/`: `main.py`, `agent.py`, `models.py`, `tools.py`, `prompts/prompt.md`)
- **Write-ups:** `output/` (`harness.md`, `design.md`, `usability.md`, `app_check.html`, `audit_trail.json`)
- **Prompt log:** `AI_prompts.md`

## 1. Put the data pack in place

The database and product images are **not** in this repo. Unzip the course data pack so it looks like this:

```
hw4/
└── data/
    ├── campus_customs.db
    └── products/
```

## 2. Add your API key

```bash
cd hw4
cp .env.example .env
```

Open `.env` and fill in `OPENAI_API_KEY`. Never commit `.env` (it's already in `.gitignore`).

## 3. Run the back end (terminal 1)

```bash
cd hw4
python3 -m venv .venv             # first time only
source .venv/bin/activate
pip install -r requirements.txt   # first time only
cd backend
uvicorn main:app --reload --port 8000
```

On startup the backend adds the tables it needs (saved chats, login sessions) if they're missing. Health check: http://127.0.0.1:8000/api/health

## 4. Run the website (terminal 2)

```bash
cd hw4/frontend
npm install     # first time only
npm run dev
```

Open http://localhost:5173. Both terminals need to stay running.

**Test login:** `test@campuscustoms.yale.edu` / `password`

## More detail

See `output/harness.md` for how everything works: database fields, tools, safety rules, loop limits and the audit trail.

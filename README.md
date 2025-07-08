# Agentic Portfolio Advisor

A compact FastAPI + React demo that showcases how a small crew of GPT-4 agents can analyse and rebalance an investment portfolio.

---
## Setup

1. Clone & enter
   ```bash
   git clone https://github.com/shreyasmalhotra/agentic-advisor.git
   cd agentic-portfolio-advisor
   ```
2. Python backend (3.11)
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Front-end (Vite + React 19)
   ```bash
   cd frontend
   npm install
   ```
4. Environment
   ```bash
   cp env.example .env  # then edit with your keys
   ```

---
## Running in dev
```bash
<<<<<<< HEAD
# terminal 1 – backend
=======
# back-end
git clone https://github.com/<your-org>/agentic-advisor-backend.git
cd agentic-advisor-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # lint/test tooling

# front-end
cd frontend
npm install
```

### 2.3 Environment variables
Create `.env` in project root:
```env
OPENAI_API_KEY=<your-key>
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_KEY=<service-role-key>
```

### 2.4 Database
Run the migration script under `database_schema.sql` against your Supabase project (or `psql`). It creates:
* `portfolio_sessions`
* `chat_messages`

### 2.5 Launch services
```bash
# terminal 1 – FastAPI + agents
>>>>>>> parent of 4ef7c3e1 (Cleanup: remove unused CRA frontend; add .gitignore and env example)
uvicorn app:app --reload

# terminal 2 – front-end
cd frontend
npm run dev
```
Open http://localhost:5173 in your browser.

---
## What the app does
* Fetches live prices for the user’s holdings (Yahoo Finance)
* Shows drift vs. strategic target derived from risk score
* Generates specific buy / sell percentages
* Explains the rationale in plain English

**Not financial advice – just a learning project.** 
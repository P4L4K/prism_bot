# 📖 PRISM Storybook — Voice Assistant Platform

PRISM Storybook is an interactive, voice-first AI assistant application that transforms chat threads into living 3D storybooks.

---

## 🚀 Quick Start

### 1. Local Development (Standard Setup)

#### **Backend Setup (Python FastAPI)**
Ensure Python 3.9+ is installed.

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate      # On Windows
# source venv/bin/activate  # On macOS/Linux

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Download the spaCy NLP model
python -m spacy download en_core_web_sm

# 4. Launch the FastAPI server
python -m backend.server
```
The FastAPI backend server will start at `http://localhost:8000`.

#### **Frontend Setup (React + Vite)**
Ensure Node.js 18+ is installed.

```bash
# Navigate to the frontend folder
cd frontend

# Install Node packages
npm install

# Start the Vite development server
npm run dev
```
Open your browser at `http://localhost:5173`.

---

### 2. Docker Setup (Local Containerized Environment)

Run the full stack (FastAPI Backend + PostgreSQL database) with a single command:

```bash
# Build and start containers in the background
docker-compose up --build -d
```

- **Backend API**: `http://localhost:8000`
- **PostgreSQL Database**: Listening on port `5432`

To stop the containers:
```bash
docker-compose down
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string (falls back to local SQLite if omitted) | `sqlite:///data/assistant.db` |
| `OPENWEATHERMAP_API_KEY` | Weather API key for real-time forecasts | Optional |
| `NEWS_API_KEY` | NewsAPI key for news summaries | Optional |
| `PRISM_LOG_LEVEL` | Application logging verbosity | `INFO` |

---

## 📁 Project Structure

```text
├── backend/
│   └── api/             # FastAPI REST endpoints, SSE routes, and server runner
├── app/
│   ├── core/            # Pipeline orchestrator and settings configuration
│   ├── db/              # SQLAlchemy models, sessions, and repository functions
│   ├── modules/         # Skill handlers (Weather, News, Reminders, Chitchat)
│   ├── nlp/             # Intent classification and entity extraction
│   └── speech/          # Voice processing (STT, TTS, openWakeWord)
├── frontend/
│   ├── src/
│   │   ├── pages/       # Storybook Dashboard, Bookshelf, Settings
│   │   ├── store/       # Zustand global state manager
│   │   └── hooks/       # Server-Sent Events (useSSE) real-time hook
├── Dockerfile           # Backend container build configuration
└── docker-compose.yml   # Multi-container orchestration (FastAPI + PostgreSQL)
```

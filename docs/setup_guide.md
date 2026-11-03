# NexusFlow Setup Guide

## Prerequisites
- Python 3.11.x
- Node.js 18+ and npm 9+
- Windows PowerShell or Bash terminal

## 1. Backend Setup
Navigate to the backend directory:
```powershell
cd backend
pip install -r requirements.txt
```

Initialize data, train the baseline model, and ingest knowledge collateral:
```powershell
python scripts/seed_data.py
python scripts/train_model.py
python scripts/ingest_knowledge.py
```

Run test suite:
```powershell
pytest
```

Start the FastAPI backend service:
```powershell
uvicorn app.main:app --reload --port 8000
```
Backend runs at: `http://localhost:8000` (Docs at `http://localhost:8000/docs`)

## 2. Frontend Setup
In a new terminal window:
```powershell
cd frontend
npm install
npm run dev
```
Frontend runs at: `http://localhost:5173`

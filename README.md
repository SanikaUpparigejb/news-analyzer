# News Analyzer — AI-Powered NLP Web Application

A full-stack NLP application that summarizes news articles, classifies topics,
and detects sentiment using HuggingFace Transformer models.

## Stack
- **Backend:** FastAPI, SQLAlchemy, SQLite, JWT Auth
- **AI/ML:** DistilBART-XSum, BART-large-MNLI, DistilBERT-SST2
- **Frontend:** Streamlit

## Setup

### 1. Clone the repo
git clone https://github.com/yourusername/news-summarizer.git
cd news-summarizer

### 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

### 3. Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && pip install -r requirements.txt

### 4. Set environment variables
Copy backend/.env.example to backend/.env and fill in values.

### 5. Run backend
cd backend
uvicorn main:app --reload --port 8000

### 6. Run frontend (new terminal)
cd frontend
streamlit run app.py

## Status
🚧 Under active development
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import timedelta

import models
import auth
from database import engine, get_db
from model import summarize, classify_topic, analyze_sentiment
import time
from concurrent.futures import ThreadPoolExecutor

# Create all tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="News Analyzer API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str

class ArticleRequest(BaseModel):
    text: str
    title: str = ""

class AnalysisResponse(BaseModel):
    id: int
    summary: str
    topic: dict
    sentiment: dict
    word_count: int
    processing_time: float

class HistoryItem(BaseModel):
    id: int
    article_title: str
    article_snippet: str
    summary: str
    topic: str
    topic_confidence: float
    sentiment: str
    word_count: int
    created_at: str


# ── Auth routes ────────────────────────────────────────────────────────────────

@app.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if auth.get_user_by_username(db, req.username):
        raise HTTPException(status_code=400, detail="Username already taken.")
    if auth.get_user_by_email(db, req.email):
        raise HTTPException(status_code=400, detail="Email already registered.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    user = auth.create_user(db, req.username, req.email, req.password)
    return {"message": f"Account created! Welcome, {user.username} 🎉"}


@app.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = auth.authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer", "username": user.username}


@app.get("/me")
def get_profile(current_user: models.User = Depends(auth.get_current_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "member_since": str(current_user.created_at)[:10]
    }


# ── Analysis route (protected) ─────────────────────────────────────────────────

@app.post("/analyze", response_model=AnalysisResponse)
def analyze_article(
    request: ArticleRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)  # protected
):
    text = request.text.strip()

    if len(text.split()) < 50:
        raise HTTPException(status_code=400, detail="Article too short. Need at least 50 words.")

    start = time.time()

    try:
        # Run all three models concurrently instead of sequentially.
        # Each model call is CPU-bound and independent of the others, so
        # running them on separate threads lets them execute in parallel
        # (Python releases the GIL during PyTorch's underlying C++ ops),
        # cutting total wall-clock time roughly to the duration of the
        # slowest single model instead of the sum of all three.
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_summary   = executor.submit(summarize, text)
            future_topic     = executor.submit(classify_topic, text)
            future_sentiment = executor.submit(analyze_sentiment, text)

            summary   = future_summary.result()
            topic     = future_topic.result()
            sentiment = future_sentiment.result()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model error: {str(e)}")

    elapsed = round(time.time() - start, 2)

    # ── Save to database ──────────────────────────────────────────────────────
    record = models.Analysis(
        user_id          = current_user.id,
        article_title    = request.title or "Untitled",
        article_snippet  = text[:300],
        summary          = summary,
        topic            = topic["top_topic"],
        topic_confidence = topic["confidence"],
        sentiment        = sentiment["sentiment"],
        sentiment_confidence = sentiment["confidence"],
        word_count       = len(text.split()),
        processing_time  = elapsed
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return AnalysisResponse(
        id=record.id,
        summary=summary,
        topic=topic,
        sentiment=sentiment,
        word_count=len(text.split()),
        processing_time=elapsed
    )


# ── History route (protected) ──────────────────────────────────────────────────

@app.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    records = (
        db.query(models.Analysis)
        .filter(models.Analysis.user_id == current_user.id)
        .order_by(models.Analysis.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": r.id,
            "article_title": r.article_title,
            "article_snippet": r.article_snippet,
            "summary": r.summary,
            "topic": r.topic,
            "topic_confidence": r.topic_confidence,
            "sentiment": r.sentiment,
            "word_count": r.word_count,
            "created_at": str(r.created_at)[:16]
        }
        for r in records
    ]


@app.delete("/history/{analysis_id}")
def delete_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    record = db.query(models.Analysis).filter(
        models.Analysis.id == analysis_id,
        models.Analysis.user_id == current_user.id  # users can only delete their own
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    db.delete(record)
    db.commit()
    return {"message": "Deleted successfully."}


@app.get("/health")
def health():
    return {"status": "healthy"}
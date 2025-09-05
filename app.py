import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from db import Base, engine, SessionLocal
from models import Question, Score
from schemas import QuestionOut, AnswerIn, CheckOut, ScoreIn, ScoreOut
from auth import require_user
from sqlalchemy import func

app = FastAPI(title="Quiz Battle Online API")

allow_origins_env = os.getenv("ALLOW_ORIGINS", "*")
allow_origins = (
    [o.strip() for o in allow_origins_env.split(",")] 
    if allow_origins_env != "*" else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"]
    expose_headers=["*"], 
    allow_credentials=False,      
    max_age=86400,                
)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"ok": True}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/question", response_model=QuestionOut)
def get_question(db: Session = Depends(get_db), user=Depends(require_user)):
    # Fetch a random question
    q = db.execute(select(Question).order_by(func.random()).limit(1)).scalar_one_or_none()
    if not q:
        raise HTTPException(404, "No questions found")
    return q

@app.post("/answer", response_model=CheckOut)
def check_answer(payload: AnswerIn, db: Session = Depends(get_db), user=Depends(require_user)):
    q = db.get(Question, payload.question_id)
    if not q:
        raise HTTPException(404, "Question not found")
    correct = (payload.choice_index == q.answer)
    return {"correct": bool(correct), "correct_index": q.answer}

@app.post("/score", response_model=ScoreOut)
def submit_score(payload: ScoreIn, db: Session = Depends(get_db), user=Depends(require_user)):
    uid, email, name = user
    points = max(0, int(payload.points))
    s = Score(firebase_uid=uid, username=payload.username or (name or "Player"), points=points)
    db.add(s)
    db.commit()
    return {"username": s.username, "points": s.points}

@app.get("/ranking", response_model=list[ScoreOut])
def ranking(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Score.username, Score.points)
        .order_by(Score.points.desc(), Score.created_at.asc())
        .limit(10)
    ).all()
    return [{"username": r[0], "points": r[1]} for r in rows]

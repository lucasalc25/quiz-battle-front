from pydantic import BaseModel
from typing import List

class QuestionOut(BaseModel):
    id: int
    question: str
    options: List[str]
    class Config:
        from_attributes = True

class AnswerIn(BaseModel):
    question_id: int
    choice_index: int

class CheckOut(BaseModel):
    correct: bool
    correct_index: int

class ScoreIn(BaseModel):
    username: str
    points: int

class ScoreOut(BaseModel):
    username: str
    points: int

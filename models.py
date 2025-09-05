from sqlalchemy import Column, Integer, Text, DateTime, func, ARRAY
from db import Base

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    options = Column(ARRAY(Text), nullable=False)
    answer = Column(Integer, nullable=False)  # index of correct option

class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True)
    firebase_uid = Column(Text, nullable=False)
    username = Column(Text, nullable=False)
    points = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

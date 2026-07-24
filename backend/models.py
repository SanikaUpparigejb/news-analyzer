from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String, unique=True, index=True, nullable=False)
    email      = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # One user → many analyses
    analyses   = relationship("Analysis", back_populates="owner")


class Analysis(Base):
    __tablename__ = "analyses"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    article_title   = Column(String, default="Untitled")
    article_snippet = Column(Text)        # first 300 chars of original text
    summary         = Column(Text)
    topic           = Column(String)
    topic_confidence= Column(Float)
    sentiment       = Column(String)
    sentiment_confidence = Column(Float)
    word_count      = Column(Integer)
    processing_time = Column(Float)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="analyses")
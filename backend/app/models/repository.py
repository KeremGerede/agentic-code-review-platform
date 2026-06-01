from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    owner = Column(String(255), nullable=False)
    repo_name = Column(String(255), nullable=False)
    full_name = Column(String(512), nullable=False, unique=True)
    default_branch = Column(String(255), default="main")
    github_url = Column(String(512), nullable=False)
    notification_emails = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rules = relationship("Rule", back_populates="repository", cascade="all, delete-orphan")
    analysis_runs = relationship("AnalysisRun", back_populates="repository", cascade="all, delete-orphan")

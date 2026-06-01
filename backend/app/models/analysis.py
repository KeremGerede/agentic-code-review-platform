from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    commit_sha = Column(String(40), nullable=False)
    branch = Column(String(255), nullable=False)
    author = Column(String(255), nullable=True)
    status = Column(String(50), default="running")        # running | completed | failed
    summary = Column(Text, nullable=True)
    risk_level = Column(String(50), nullable=True)        # low | medium | high | critical
    total_files_analyzed = Column(Integer, default=0)
    total_findings = Column(Integer, default=0)
    email_status = Column(String(50), default="pending")  # pending | sent | failed
    email_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    repository = relationship("Repository", back_populates="analysis_runs")
    findings = relationship("Finding", back_populates="analysis_run", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    analysis_run_id = Column(Integer, ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(512), nullable=False)
    line_number = Column(Integer, nullable=True)
    rule_title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    issue = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=False)
    code_snippet = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis_run = relationship("AnalysisRun", back_populates="findings")

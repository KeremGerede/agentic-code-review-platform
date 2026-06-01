from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, field_validator


# ── Gemini raw output schemas ──────────────────────────────────────────────────

class GeminiFinding(BaseModel):
    file_path: str
    line_number: Optional[int] = None
    rule_title: str
    category: Literal[
        "security", "code_quality", "architecture",
        "testing", "performance", "maintainability", "style", "other"
    ]
    severity: Literal["info", "warning", "high", "critical"]
    issue: str
    explanation: str
    suggestion: str
    code_snippet: Optional[str] = None


class GeminiAnalysisResponse(BaseModel):
    summary: str
    risk_level: Literal["low", "medium", "high", "critical"]
    total_findings: int
    findings: List[GeminiFinding]

    @field_validator("total_findings")
    @classmethod
    def findings_count_matches(cls, v, info):
        # Soft validation — trust Gemini count but allow mismatch
        return v


# ── API response schemas ───────────────────────────────────────────────────────

class FindingRead(BaseModel):
    id: int
    analysis_run_id: int
    file_path: str
    line_number: Optional[int] = None
    rule_title: str
    category: str
    severity: str
    issue: str
    explanation: str
    suggestion: str
    code_snippet: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisRunRead(BaseModel):
    id: int
    repository_id: int
    commit_sha: str
    branch: str
    author: Optional[str] = None
    status: str
    summary: Optional[str] = None
    risk_level: Optional[str] = None
    total_files_analyzed: int
    total_findings: int
    email_status: str
    email_error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    findings: List[FindingRead] = []

    model_config = {"from_attributes": True}

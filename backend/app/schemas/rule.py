from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel

CategoryType = Literal[
    "security", "code_quality", "architecture",
    "testing", "performance", "maintainability", "style", "other"
]

SeverityType = Literal["info", "warning", "high", "critical"]


class RuleCreate(BaseModel):
    title: str
    description: str
    category: CategoryType = "other"
    severity: SeverityType = "warning"
    is_enabled: bool = True
    repository_id: Optional[int] = None


class RuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[CategoryType] = None
    severity: Optional[SeverityType] = None
    is_enabled: Optional[bool] = None
    repository_id: Optional[int] = None


class RuleRead(BaseModel):
    id: int
    title: str
    description: str
    category: str
    severity: str
    is_enabled: bool
    repository_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

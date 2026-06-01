from typing import Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl


class RepositoryCreate(BaseModel):
    name: str
    owner: str
    repo_name: str
    full_name: str
    default_branch: str = "main"
    github_url: str
    notification_emails: Optional[str] = None


class RepositoryRead(BaseModel):
    id: int
    name: str
    owner: str
    repo_name: str
    full_name: str
    default_branch: str
    github_url: str
    notification_emails: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

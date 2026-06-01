from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.repository import Repository
from app.schemas.repository import RepositoryCreate, RepositoryRead

router = APIRouter(prefix="/api/repositories", tags=["Repositories"])


@router.get("", response_model=List[RepositoryRead])
def list_repositories(db: Session = Depends(get_db)):
    return db.query(Repository).order_by(Repository.created_at.desc()).all()


@router.post("", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED)
def create_repository(payload: RepositoryCreate, db: Session = Depends(get_db)):
    existing = db.query(Repository).filter(Repository.full_name == payload.full_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Repository '{payload.full_name}' already exists.",
        )
    repo = Repository(**payload.model_dump())
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


@router.get("/{repository_id}", response_model=RepositoryRead)
def get_repository(repository_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return repo


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repository(repository_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    db.delete(repo)
    db.commit()

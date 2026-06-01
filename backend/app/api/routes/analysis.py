from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.analysis import AnalysisRun
from app.schemas.analysis import AnalysisRunRead

router = APIRouter(tags=["Analysis"])


@router.get("/api/analysis", response_model=List[AnalysisRunRead])
def list_analysis_runs(db: Session = Depends(get_db)):
    runs = (
        db.query(AnalysisRun)
        .options(joinedload(AnalysisRun.findings))
        .order_by(AnalysisRun.created_at.desc())
        .limit(100)
        .all()
    )
    return runs


@router.get("/api/analysis/{analysis_id}", response_model=AnalysisRunRead)
def get_analysis_run(analysis_id: int, db: Session = Depends(get_db)):
    run = (
        db.query(AnalysisRun)
        .options(joinedload(AnalysisRun.findings))
        .filter(AnalysisRun.id == analysis_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found.")
    return run


@router.get("/api/repositories/{repository_id}/analysis", response_model=List[AnalysisRunRead])
def get_repository_analysis(repository_id: int, db: Session = Depends(get_db)):
    runs = (
        db.query(AnalysisRun)
        .options(joinedload(AnalysisRun.findings))
        .filter(AnalysisRun.repository_id == repository_id)
        .order_by(AnalysisRun.created_at.desc())
        .all()
    )
    return runs

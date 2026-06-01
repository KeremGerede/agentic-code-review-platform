import logging
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.core.security import verify_github_signature
from app.db.database import get_db
from app.models.repository import Repository
from app.models.analysis import AnalysisRun, Finding
from app.models.rule import Rule
from app.services import github_service, analysis_agent, email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post("/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(request: Request, db: Session = Depends(get_db)):
    # ── 1. Read raw body (must be done before .json()) ────────────────────────
    raw_body = await request.body()

    # ── 2. Verify signature ───────────────────────────────────────────────────
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_github_signature(raw_body, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature.",
        )

    # ── 3. Only handle push events ────────────────────────────────────────────
    event_type = request.headers.get("X-GitHub-Event", "")
    if event_type != "push":
        logger.info("Ignoring non-push event: %s", event_type)
        return {"message": f"Event '{event_type}' ignored."}

    payload = await request.json()

    # ── 4. Extract push event fields ─────────────────────────────────────────
    gh_repo = payload.get("repository", {})
    owner = gh_repo.get("owner", {}).get("login", "")
    repo_name = gh_repo.get("name", "")
    full_name = gh_repo.get("full_name", "")
    github_url = gh_repo.get("html_url", "")
    default_branch = gh_repo.get("default_branch", "main")

    pushed_ref = payload.get("ref", "")
    pushed_branch = pushed_ref.replace("refs/heads/", "")

    before_sha = payload.get("before", "")
    after_sha = payload.get("after", "")

    head_commit = payload.get("head_commit") or {}
    author = (
        head_commit.get("author", {}).get("name")
        or head_commit.get("committer", {}).get("name")
        or "unknown"
    )

    if not owner or not repo_name or not after_sha:
        logger.warning("Push event missing required fields.")
        return {"message": "Push event missing required fields."}

    logger.info("Push event: %s branch=%s commit=%s", full_name, pushed_branch, after_sha[:7])

    # ── 5. Find or create Repository ─────────────────────────────────────────
    repo = db.query(Repository).filter(Repository.full_name == full_name).first()
    if not repo:
        repo = Repository(
            name=repo_name,
            owner=owner,
            repo_name=repo_name,
            full_name=full_name,
            default_branch=default_branch,
            github_url=github_url,
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
        logger.info("Auto-created repository: %s", full_name)

    # ── 6. Create AnalysisRun ─────────────────────────────────────────────────
    run = AnalysisRun(
        repository_id=repo.id,
        commit_sha=after_sha,
        branch=pushed_branch,
        author=author,
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    logger.info("Created AnalysisRun id=%d", run.id)

    try:
        # ── 7. Fetch changed files ────────────────────────────────────────────
        changed_files = github_service.fetch_changed_files(owner, repo_name, before_sha, after_sha)

        # ── 8. Load rules (global + repo-specific) ────────────────────────────
        rules_query = db.query(Rule).filter(
            Rule.is_enabled == True,
            (Rule.repository_id == None) | (Rule.repository_id == repo.id),
        )
        rules = rules_query.all()
        rules_data = [
            {
                "title": r.title,
                "description": r.description,
                "category": r.category,
                "severity": r.severity,
            }
            for r in rules
        ]

        # ── 9. Run agentic analysis ───────────────────────────────────────────
        repository_info = {
            "full_name": full_name,
            "owner": owner,
            "repo_name": repo_name,
            "github_url": github_url,
        }
        commit_info = {
            "branch": pushed_branch,
            "commit_sha": after_sha,
            "author": author,
        }

        result = analysis_agent.run_analysis(
            repository_info=repository_info,
            commit_info=commit_info,
            rules=rules_data,
            changed_files=changed_files,
        )

        # ── 10. Save findings ─────────────────────────────────────────────────
        for f in result.findings:
            finding = Finding(
                analysis_run_id=run.id,
                file_path=f.file_path,
                line_number=f.line_number,
                rule_title=f.rule_title,
                category=f.category,
                severity=f.severity,
                issue=f.issue,
                explanation=f.explanation,
                suggestion=f.suggestion,
                code_snippet=f.code_snippet,
            )
            db.add(finding)

        # ── 11. Mark run completed ────────────────────────────────────────────
        run.status = "completed"
        run.summary = result.summary
        run.risk_level = result.risk_level
        run.total_files_analyzed = len(changed_files)
        run.total_findings = result.total_findings
        run.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(run)
        logger.info("AnalysisRun id=%d completed: risk=%s findings=%d", run.id, run.risk_level, run.total_findings)

    except Exception as exc:
        logger.error("Analysis failed for run id=%d: %s", run.id, exc, exc_info=True)
        run.status = "failed"
        run.summary = f"Analysis failed: {str(exc)}"
        run.completed_at = datetime.utcnow()
        db.commit()
        return {"message": "Analysis failed.", "run_id": run.id}

    # ── 12. Send email (failure does not fail the run) ────────────────────────
    try:
        run_data = {
            "risk_level": run.risk_level,
            "branch": run.branch,
            "commit_sha": run.commit_sha,
            "author": run.author,
            "summary": run.summary,
            "total_files_analyzed": run.total_files_analyzed,
            "total_findings": run.total_findings,
            "status": run.status,
        }
        repo_data = {
            "full_name": repo.full_name,
            "notification_emails": repo.notification_emails,
        }
        findings_data = [
            {
                "file_path": f.file_path,
                "line_number": f.line_number,
                "rule_title": f.rule_title,
                "category": f.category,
                "severity": f.severity,
                "issue": f.issue,
                "explanation": f.explanation,
                "suggestion": f.suggestion,
                "code_snippet": f.code_snippet,
            }
            for f in run.findings
        ]
        email_service.send_report(run_data, findings_data, repo_data)
        run.email_status = "sent"
        db.commit()
    except Exception as email_exc:
        logger.error("Email sending failed for run id=%d: %s", run.id, email_exc)
        run.email_status = "failed"
        run.email_error = str(email_exc)
        db.commit()

    return {"message": "Analysis completed.", "run_id": run.id}

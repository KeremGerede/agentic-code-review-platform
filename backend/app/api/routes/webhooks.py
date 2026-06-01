import logging
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy import or_
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

    # ── 1. Log arrival immediately (before anything can fail) ─────────────────
    logger.info(
        "⬇️  Webhook request received — method=%s path=%s",
        request.method, request.url.path,
    )
    logger.info(
        "Webhook headers — X-GitHub-Event=%s X-GitHub-Delivery=%s Content-Type=%s",
        request.headers.get("X-GitHub-Event", "MISSING"),
        request.headers.get("X-GitHub-Delivery", "MISSING"),
        request.headers.get("Content-Type", "MISSING"),
    )

    # ── 2. Read raw body (MUST happen before request.json()) ──────────────────
    raw_body = await request.body()
    logger.info("Webhook raw body length: %d bytes", len(raw_body))

    if not raw_body:
        logger.warning("Webhook received with empty body — ignoring.")
        return {"message": "Empty body."}

    # ── 3. Verify signature ───────────────────────────────────────────────────
    signature = request.headers.get("X-Hub-Signature-256")
    logger.info("X-Hub-Signature-256 present: %s", "YES" if signature else "NO")

    if not verify_github_signature(raw_body, signature):
        logger.error(
            "❌ Webhook signature verification failed. "
            "Check that GITHUB_WEBHOOK_SECRET matches the secret set in GitHub."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature.",
        )

    logger.info("✅ Webhook signature verified.")

    # ── 4. Only handle push events ────────────────────────────────────────────
    event_type = request.headers.get("X-GitHub-Event", "")
    logger.info("GitHub event type: %s", event_type)

    if event_type != "push":
        logger.info("Ignoring non-push event: %s", event_type)
        return {"message": f"Event '{event_type}' ignored."}

    # ── 5. Parse payload ──────────────────────────────────────────────────────
    try:
        payload = await request.json()
    except Exception as exc:
        logger.error("Failed to parse webhook JSON payload: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

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
        or payload.get("pusher", {}).get("name")
        or "unknown"
    )

    logger.info(
        "Push payload — repo=%s branch=%s before=%s after=%s author=%s",
        full_name, pushed_branch,
        before_sha[:7] if before_sha else "N/A",
        after_sha[:7] if after_sha else "N/A",
        author,
    )

    if not owner or not repo_name or not after_sha:
        logger.warning(
            "Push event missing required fields — owner=%r repo_name=%r after_sha=%r",
            owner, repo_name, after_sha,
        )
        return {"message": "Push event missing required fields."}

    # ── 6. Find or create Repository ──────────────────────────────────────────
    repo = db.query(Repository).filter(Repository.full_name == full_name).first()
    if repo:
        logger.info("Repository already exists: %s (id=%d)", full_name, repo.id)
    else:
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
        logger.info("✅ Auto-created new repository: %s (id=%d)", full_name, repo.id)

    # ── 7. Create AnalysisRun immediately (visible in UI even if AI fails) ────
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
    logger.info("✅ Created AnalysisRun id=%d (status=running)", run.id)

    # ── 8. Run analysis pipeline (errors are caught, run is marked failed) ────
    try:
        changed_files = github_service.fetch_changed_files(
            owner, repo_name, before_sha, after_sha
        )
        logger.info("Fetched %d analyzable file(s).", len(changed_files))

        # Load enabled global rules + enabled repo-specific rules
        rules_qs = db.query(Rule).filter(
            Rule.is_enabled == True,
            or_(Rule.repository_id == None, Rule.repository_id == repo.id),
        )
        active_rules = rules_qs.all()
        logger.info(
            "Loaded %d active rule(s) (global + repo-specific).", len(active_rules)
        )

        rules_data = [
            {
                "title": r.title,
                "description": r.description,
                "category": r.category,
                "severity": r.severity,
            }
            for r in active_rules
        ]

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

        # Save findings
        for f in result.findings:
            db.add(Finding(
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
            ))

        run.status = "completed"
        run.summary = result.summary
        run.risk_level = result.risk_level
        run.total_files_analyzed = len(changed_files)
        run.total_findings = result.total_findings
        run.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(run)
        logger.info(
            "✅ AnalysisRun id=%d completed — risk=%s findings=%d",
            run.id, run.risk_level, run.total_findings,
        )

    except Exception as exc:
        logger.error(
            "❌ Analysis pipeline failed for run id=%d: %s",
            run.id, exc, exc_info=True,
        )
        run.status = "failed"
        run.summary = f"Analysis failed: {str(exc)}"
        run.completed_at = datetime.utcnow()
        db.commit()
        # Still send the (failed) response to GitHub so it doesn't retry endlessly
        return {"message": "Analysis failed — run saved.", "run_id": run.id}

    # ── 9. Send email (failure must NOT affect run status) ────────────────────
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
        logger.info("✅ Report email sent for run id=%d.", run.id)
    except Exception as email_exc:
        logger.error(
            "❌ Email sending failed for run id=%d: %s", run.id, email_exc
        )
        run.email_status = "failed"
        run.email_error = str(email_exc)
        db.commit()

    return {"message": "Analysis completed.", "run_id": run.id}

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import Base, engine, get_db

# Import models so SQLAlchemy registers them before create_all
from app.models import repository, rule, analysis  # noqa: F401
from app.models.repository import Repository
from app.models.rule import Rule
from app.models.analysis import AnalysisRun

from app.api.routes import repositories, rules, analysis as analysis_routes, webhooks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="AI Code Review Agent",
    description="Agentic AI-powered GitHub code review platform.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(repositories.router)
app.include_router(rules.router)
app.include_router(analysis_routes.router)
app.include_router(webhooks.router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


@app.get("/api/debug/health", tags=["Debug"])
def debug_health(db: Session = Depends(get_db)):
    """
    Diagnostic endpoint — shows system state without exposing secrets.
    Safe to call at any time during local development.
    """
    db_ok = False
    repo_count = 0
    rule_count = 0
    run_count = 0

    try:
        repo_count = db.query(Repository).count()
        rule_count = db.query(Rule).count()
        run_count = db.query(AnalysisRun).count()
        db_ok = True
    except Exception as exc:
        logger.error("debug/health DB query failed: %s", exc)

    # Show DB path but not the full URL (might contain credentials in postgres)
    db_url_display = settings.DATABASE_URL
    if "@" in db_url_display:
        db_url_display = db_url_display.split("@")[-1]  # hide user:pass

    return {
        "backend_status": "ok",
        "database_connected": db_ok,
        "database_url": db_url_display,
        "repository_count": repo_count,
        "rule_count": rule_count,
        "analysis_run_count": run_count,
        "gemini_api_key_set": bool(settings.GEMINI_API_KEY),
        "github_token_set": bool(settings.GITHUB_TOKEN),
        "github_webhook_secret_set": bool(settings.GITHUB_WEBHOOK_SECRET),
        "smtp_configured": bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD),
        "debug_skip_signature": settings.DEBUG_SKIP_WEBHOOK_SIGNATURE_CHECK,
        "webhook_endpoint": "POST /api/webhooks/github",
    }

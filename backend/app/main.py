import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import Base, engine

# Import models so SQLAlchemy registers them before create_all
from app.models import repository, rule, analysis  # noqa: F401

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

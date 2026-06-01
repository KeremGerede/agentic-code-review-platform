import logging
from typing import List, Dict, Any

import httpx

from app.core.config import settings
from app.utils.file_filters import filter_files, truncate_patch

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
ZERO_SHA = "0" * 40  # SHA sent by GitHub when a branch is created from scratch


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get(url: str) -> dict:
    """Make a single authenticated GET request and return parsed JSON."""
    logger.info("GitHub API GET: %s", url)
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=_headers())
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "GitHub API error %s for %s: %s",
            exc.response.status_code, url, exc.response.text[:300],
        )
        raise RuntimeError(
            f"GitHub API returned {exc.response.status_code} for {url}"
        ) from exc
    except httpx.RequestError as exc:
        logger.error("GitHub request failed for %s: %s", url, exc)
        raise RuntimeError("Failed to reach GitHub API") from exc
    return response.json()


def _files_from_commit(owner: str, repo: str, sha: str) -> List[Dict]:
    """
    Fetch changed files from a single commit.
    Used as fallback when before-SHA is all zeros (first push / new branch).
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits/{sha}"
    data = _get(url)
    files = data.get("files", [])
    logger.info("Single-commit endpoint returned %d file(s) for %s.", len(files), sha[:7])
    return files


def _files_from_compare(owner: str, repo: str, before: str, after: str) -> List[Dict]:
    """Fetch changed files using the compare endpoint."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/compare/{before}...{after}"
    data = _get(url)
    files = data.get("files", [])
    logger.info("Compare endpoint returned %d file(s).", len(files))
    return files


def fetch_changed_files(owner: str, repo: str, before: str, after: str) -> List[Dict[str, Any]]:
    """
    Return a normalized list of changed file dicts suitable for the analysis agent.

    Handles two cases:
    - Normal push: uses the compare endpoint (before...after).
    - First push / new branch (before == ZERO_SHA): uses the single commit endpoint.
    """
    if before == ZERO_SHA or not before:
        logger.info(
            "before SHA is all-zeros — first push or new branch. "
            "Using single-commit endpoint for %s.", after[:7]
        )
        raw_files = _files_from_commit(owner, repo, after)
    else:
        raw_files = _files_from_compare(owner, repo, before, after)

    logger.info("Total raw files from GitHub: %d", len(raw_files))

    filtered = filter_files(raw_files)
    logger.info("%d file(s) remain after filtering.", len(filtered))

    normalized = []
    for f in filtered:
        raw_patch = f.get("patch", "")
        patch, truncated = truncate_patch(raw_patch)
        normalized.append({
            "filename": f.get("filename", ""),
            "status": f.get("status", "modified"),
            "additions": f.get("additions", 0),
            "deletions": f.get("deletions", 0),
            "changes": f.get("changes", 0),
            "patch": patch,
            "patch_truncated": truncated,
        })

    return normalized

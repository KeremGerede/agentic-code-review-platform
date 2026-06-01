import logging
from typing import List, Dict, Any

import httpx

from app.core.config import settings
from app.utils.file_filters import filter_files, truncate_patch

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_changed_files(owner: str, repo: str, before: str, after: str) -> List[Dict[str, Any]]:
    """
    Use GitHub compare API to get the list of changed files between two commits.
    Returns a normalized list of file dicts ready for the analysis agent.
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/compare/{before}...{after}"
    logger.info("Fetching GitHub compare: %s", url)

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=_headers())
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error("GitHub API error %s: %s", exc.response.status_code, exc.response.text)
        raise RuntimeError(f"GitHub API returned {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        logger.error("GitHub request failed: %s", exc)
        raise RuntimeError("Failed to reach GitHub API") from exc

    data = response.json()
    raw_files: List[Dict] = data.get("files", [])
    logger.info("GitHub compare returned %d file(s).", len(raw_files))

    # Filter out binaries, lock files, generated paths, etc.
    filtered = filter_files(raw_files)
    logger.info("%d file(s) remain after filtering.", len(filtered))

    normalized = []
    for f in filtered:
        raw_patch = f.get("patch", "")
        patch, truncated = truncate_patch(raw_patch)
        normalized.append({
            "filename": f.get("filename", ""),
            "status": f.get("status", "modified"),   # added | modified | removed | renamed
            "additions": f.get("additions", 0),
            "deletions": f.get("deletions", 0),
            "changes": f.get("changes", 0),
            "patch": patch,
            "patch_truncated": truncated,
        })

    return normalized

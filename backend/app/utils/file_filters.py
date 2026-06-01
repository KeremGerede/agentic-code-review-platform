import os
from typing import List

# ── Extensions that are safe to analyze ───────────────────────────────────────
ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".cs", ".go", ".php", ".rb",
    ".cpp", ".c", ".h", ".html", ".css",
    ".scss", ".sql", ".json", ".yml", ".yaml", ".md",
}

# ── File names to always ignore ────────────────────────────────────────────────
IGNORED_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
}

# ── Path fragments that indicate generated/tooling directories ─────────────────
IGNORED_PATH_FRAGMENTS = [
    "node_modules/",
    "dist/",
    "build/",
    ".git/",
    "__pycache__/",
    ".next/",
    ".vite/",
    "coverage/",
    ".gradle/",
    ".idea/",
    ".vscode/",
    "vendor/",
    "target/",
    "out/",
    "bin/",
    "obj/",
    "migrations/",          # auto-generated DB migrations can be noisy
]

# ── Size limits ────────────────────────────────────────────────────────────────
MAX_PATCH_CHARS = 8_000    # per file patch
MAX_FILES = 30             # total files sent to Gemini


def is_analyzable(filename: str) -> bool:
    """Return True if the file should be included in AI analysis."""
    # Check ignored filenames
    basename = os.path.basename(filename)
    if basename in IGNORED_FILENAMES:
        return False

    # Check ignored path fragments
    normalized = filename.replace("\\", "/")
    for fragment in IGNORED_PATH_FRAGMENTS:
        if fragment in normalized:
            return False

    # Check extension
    _, ext = os.path.splitext(filename)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        return False

    return True


def filter_files(files: List[dict]) -> List[dict]:
    """
    Filter a list of GitHub file objects.
    Each object is expected to have at least a 'filename' key.
    Returns only analyzable files, capped at MAX_FILES.
    """
    result = []
    for f in files:
        if is_analyzable(f.get("filename", "")):
            result.append(f)
        if len(result) >= MAX_FILES:
            break
    return result


def truncate_patch(patch: str | None) -> tuple[str, bool]:
    """
    Truncate a patch string if it exceeds MAX_PATCH_CHARS.
    Returns (possibly_truncated_patch, was_truncated).
    """
    if not patch:
        return ("", False)
    if len(patch) <= MAX_PATCH_CHARS:
        return (patch, False)
    return (patch[:MAX_PATCH_CHARS] + "\n... [TRUNCATED]", True)

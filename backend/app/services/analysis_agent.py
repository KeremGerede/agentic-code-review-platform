import json
import logging
from typing import List, Dict, Any

from pydantic import ValidationError

from app.schemas.analysis import GeminiAnalysisResponse
from app.services import gemini_service

logger = logging.getLogger(__name__)


def _build_prompt(
    repository_info: Dict[str, Any],
    commit_info: Dict[str, Any],
    rules: List[Dict[str, Any]],
    changed_files: List[Dict[str, Any]],
) -> str:
    rules_text = "\n".join(
        f"- [{r['severity'].upper()}] {r['title']} (category: {r['category']}): {r['description']}"
        for r in rules
    )

    files_text_parts = []
    for f in changed_files:
        patch = f.get("patch", "")
        truncated = f.get("patch_truncated", False)
        status = f.get("status", "modified")
        note = " [PATCH TRUNCATED DUE TO SIZE]" if truncated else ""
        files_text_parts.append(
            f"### File: {f['filename']} (status: {status}){note}\n"
            f"Additions: {f['additions']}, Deletions: {f['deletions']}\n"
            f"Patch:\n{patch if patch else '(no patch available)'}"
        )
    files_text = "\n\n".join(files_text_parts)

    prompt = f"""You are an autonomous senior code review agent.

Your goal is to analyze GitHub code changes according to company-defined rules, detect violations, explain their impact, and suggest fixes.

Instructions:
- Analyze ONLY the changed files and patches provided below.
- Apply ONLY the provided rules. Do not invent additional rules.
- Do not invent files or line numbers. If the line number is unknown, return null.
- If there are no issues found, return an empty findings array.
- Return ONLY valid JSON. Do not use markdown. Do not include text before or after the JSON.
- Each finding must be practical, specific, and directly traceable to the provided patch.
- Prefer fewer high-quality findings over many vague ones.
- Assign severity based on the rule's declared severity and the actual risk in context.

---

Repository: {repository_info.get('full_name')}
Branch: {commit_info.get('branch')}
Commit: {commit_info.get('commit_sha')}
Author: {commit_info.get('author', 'unknown')}

---

Active Rules:
{rules_text if rules_text else "(No rules configured. Perform a general best-practices review.)"}

---

Changed Files:
{files_text}

---

Return your response as this exact JSON structure:

{{
  "summary": "Short paragraph summarizing what was changed and any concerns.",
  "risk_level": "low | medium | high | critical",
  "total_findings": <integer>,
  "findings": [
    {{
      "file_path": "<filename>",
      "line_number": <integer or null>,
      "rule_title": "<exact rule title from the list above>",
      "category": "security | code_quality | architecture | testing | performance | maintainability | style | other",
      "severity": "info | warning | high | critical",
      "issue": "<one sentence describing the problem>",
      "explanation": "<why this is a problem and what the risk is>",
      "suggestion": "<concrete actionable fix>",
      "code_snippet": "<the relevant code line(s) or null>"
    }}
  ]
}}
"""
    return prompt


def run_analysis(
    repository_info: Dict[str, Any],
    commit_info: Dict[str, Any],
    rules: List[Dict[str, Any]],
    changed_files: List[Dict[str, Any]],
) -> GeminiAnalysisResponse:
    """
    Main agentic analysis entrypoint.
    Builds the prompt, calls Gemini, validates and returns the structured response.
    Raises RuntimeError or ValidationError on failure.
    """
    if not changed_files:
        logger.info("No analyzable files — returning empty analysis.")
        return GeminiAnalysisResponse(
            summary="No analyzable files were found in this push.",
            risk_level="low",
            total_findings=0,
            findings=[],
        )

    prompt = _build_prompt(repository_info, commit_info, rules, changed_files)
    logger.info(
        "Running analysis for %s @ %s (%d files, %d rules)",
        repository_info.get("full_name"),
        commit_info.get("commit_sha", "")[:7],
        len(changed_files),
        len(rules),
    )

    raw = gemini_service.analyze(prompt)

    try:
        result = GeminiAnalysisResponse.model_validate(raw)
    except ValidationError as exc:
        logger.error("Gemini response failed Pydantic validation: %s", exc)
        raise ValueError(f"Gemini response schema invalid: {exc}") from exc

    # Reconcile total_findings with actual list length
    actual = len(result.findings)
    if result.total_findings != actual:
        logger.warning(
            "Gemini total_findings=%d but %d findings returned. Correcting.",
            result.total_findings, actual,
        )
        result = result.model_copy(update={"total_findings": actual})

    logger.info(
        "Analysis complete: risk=%s, findings=%d",
        result.risk_level, result.total_findings,
    )
    return result

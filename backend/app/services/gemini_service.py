import json
import logging
import re

import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure Gemini once at import time
genai.configure(api_key=settings.GEMINI_API_KEY)


def _get_model() -> genai.GenerativeModel:
    return genai.GenerativeModel(model_name=settings.GEMINI_MODEL)


def _extract_json(text: str) -> str:
    """
    Strip any markdown code fences that Gemini might wrap around JSON,
    then return the raw JSON string.
    """
    # Remove ```json ... ``` or ``` ... ```
    text = text.strip()
    pattern = r"^```(?:json)?\s*([\s\S]*?)\s*```$"
    match = re.match(pattern, text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return text


def analyze(prompt: str) -> dict:
    """
    Send prompt to Gemini and return the parsed JSON response.
    Raises ValueError if the response cannot be parsed as JSON.
    """
    model = _get_model()

    generation_config = genai.types.GenerationConfig(
        temperature=0.2,           # low randomness for structured output
        response_mime_type="application/json",
    )

    logger.info("Sending prompt to Gemini model: %s", settings.GEMINI_MODEL)

    try:
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
        )
    except Exception as exc:
        logger.error("Gemini API call failed: %s", exc)
        raise RuntimeError(f"Gemini API error: {exc}") from exc

    raw_text = response.text
    logger.debug("Gemini raw response length: %d chars", len(raw_text))

    cleaned = _extract_json(raw_text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini JSON response: %s", cleaned[:500])
        raise ValueError(f"Gemini returned invalid JSON: {exc}") from exc

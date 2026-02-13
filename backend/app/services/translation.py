import logging
import os
from typing import Dict

import httpx

logger = logging.getLogger(__name__)


class TranslationService:
    """Pilot-safe translation service.

    Returns translated text when OpenAI API key is configured; otherwise passthrough.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("TRANSLATION_MODEL", "gpt-4o-mini")

    def translate(self, text: str, source_lang: str = "auto", target_lang: str = "en") -> Dict[str, str]:
        if not text:
            return {"translated_text": "", "source_lang": source_lang, "target_lang": target_lang}
        if source_lang == target_lang:
            return {
                "translated_text": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
            }
        if not self.api_key:
            return {
                "translated_text": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
            }
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    "https://api.openai.com/v1/responses",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": (
                            f"Translate this text from '{source_lang}' to '{target_lang}'. "
                            "Return only the translated text.\n\n"
                            f"{text}"
                        ),
                    },
                )
                response.raise_for_status()
                data = response.json()
                translated_text = (data.get("output_text") or "").strip()
                if translated_text:
                    return {
                        "translated_text": translated_text,
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                    }
        except Exception as exc:
            logger.warning("Translation provider unavailable, using passthrough: %s", exc)

        return {
            "translated_text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
        }


_translation_service = None


def get_translation_service() -> TranslationService:
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service

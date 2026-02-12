from typing import Dict


class TranslationService:
    """Pilot-safe translation service.

    For V1, this returns the original text unless external providers are configured.
    """

    def translate(self, text: str, source_lang: str = "auto", target_lang: str = "en") -> Dict[str, str]:
        if not text:
            return {"translated_text": "", "source_lang": source_lang, "target_lang": target_lang}
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

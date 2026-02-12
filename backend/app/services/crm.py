import logging
from typing import Dict

logger = logging.getLogger(__name__)


class CRMService:
    """Provider-neutral CRM sync adapter for pilot environments."""

    def sync_call(self, provider: str, payload: Dict) -> Dict:
        # Pilot implementation is a stub with uniform response contract.
        logger.info("CRM sync requested provider=%s call_id=%s", provider, payload.get("call_id"))
        return {
            "provider": provider,
            "status": "queued",
            "external_id": None,
        }


_crm_service = None


def get_crm_service() -> CRMService:
    global _crm_service
    if _crm_service is None:
        _crm_service = CRMService()
    return _crm_service

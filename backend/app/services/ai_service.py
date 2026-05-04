import json
import re
from typing import Any, Dict
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("ai_service")


class AIService:
    def __init__(self) -> None:
        self._client = None
        self._mode = "rule_based"

        if settings.ANTHROPIC_API_KEY and settings.AI_MODE in ("auto", "ai"):
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                self._mode = "ai"
                logger.info("AI Service: API active (model=%s)", settings.AI_MODEL)
            except Exception as exc:
                logger.warning("AI Service: init failed (%s) → rule-based fallback", exc)
        else:
            logger.info("AI Service: rule-based mode (set ANTHROPIC_API_KEY to enable AI)")


    def classify(self, text: str) -> Dict[str, Any]:
        if self._mode == "ai":
            try:
                return self._ai_classify(text)
            except Exception as exc:
                logger.warning("AI classify failed (%s) → rule-based fallback", exc)
        return self._rule_classify(text)

    def extract(self, text: str, process_type: str) -> Dict[str, Any]:
        if self._mode == "ai":
            try:
                return self._ai_extract(text, process_type)
            except Exception as exc:
                logger.warning("AI extract failed (%s) → rule-based fallback", exc)
        return self._rule_extract(text, process_type)

    def get_mode(self) -> str:
        return self._mode


    def _ai_classify(self, text: str) -> Dict[str, Any]:
        prompt = (
            "You are a business process classifier. Analyze the text and return ONLY valid JSON.\n\n"
            "Process types: invoice | customer_request | claim | lead | support_ticket | admin_case | payment_request | other\n\n"
            'Return: {"process_type": "<type>", "confidence": <0-100>, "reasoning": "<under 100 chars>"}\n\n'
            f"Text:\n{text[:2000]}"
        )
        message = self._client.messages.create(
            model=settings.AI_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._parse_json(message.content[0].text)

    def _ai_extract(self, text: str, process_type: str) -> Dict[str, Any]:
        prompt = (
            f"Extract structured data from this {process_type} text. Return ONLY valid JSON.\n\n"
            '{\n'
            '  "name": "<string or null>",\n'
            '  "email": "<string or null>",\n'
            '  "phone": "<string or null>",\n'
            '  "date": "<YYYY-MM-DD or null>",\n'
            '  "amount": <number or null>,\n'
            '  "currency": "<string or null>",\n'
            '  "description": "<under 200 chars or null>",\n'
            '  "order_number": "<string or null>",\n'
            '  "priority": "<low|medium|high|critical>",\n'
            '  "urgency_indicators": ["<strings>"],\n'
            '  "key_entities": {"key": "value"},\n'
            '  "summary": "<one sentence under 150 chars>"\n'
            '}\n\n'
            f"Text:\n{text[:3000]}"
        )
        message = self._client.messages.create(
            model=settings.AI_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._parse_json(message.content[0].text)


    def _rule_classify(self, text: str) -> Dict[str, Any]:
        from app.agent.classifier import rule_classify
        process_type, confidence, reasoning = rule_classify(text)
        return {"process_type": process_type, "confidence": confidence, "reasoning": reasoning}

    def _rule_extract(self, text: str, process_type: str) -> Dict[str, Any]:
        from app.agent.extractor import rule_extract
        return rule_extract(text, process_type)


    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        text = text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)


ai_service = AIService()

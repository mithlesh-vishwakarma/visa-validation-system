"""Invitation Letter Analyzer."""

import re
from services.document_analyzers.base import BaseAnalyzer


class InvitationLetterAnalyzer(BaseAnalyzer):
    def analyze(self, raw_text: str, extracted_data: dict) -> dict:
        text = raw_text or ''
        inviter_name = self._extract_inviter(text)
        inviter_address = self._extract_address(text)
        invitee_name = self._extract_invitee(text)
        purpose = self._extract_purpose(text)
        visit_duration = self._extract_duration(text)
        relationship = self._extract_relationship(text)

        anomalies = self.detect_anomalies([
            (not inviter_name or inviter_name == 'N/A', "Inviter name not found"),
            (not purpose, "Purpose of visit not specified in invitation"),
            (not inviter_address or inviter_address == 'N/A', "Inviter address not found"),
        ])

        return {
            "document_type": "invitation_letter",
            "inviter_name": inviter_name,
            "inviter_address": inviter_address,
            "invitee_name": invitee_name,
            "relationship": relationship,
            "visit_purpose": purpose,
            "visit_duration": visit_duration,
            "anomalies": anomalies,
            "confidence": 0.70 if inviter_name != 'N/A' else 0.40,
        }

    def _extract_inviter(self, text: str) -> str:
        m = re.search(r'(?:sincerely|yours|signed|from|by)\s*,?\s*([A-Z][a-zA-Z\s]{2,40})', text, re.IGNORECASE)
        return m.group(1).strip() if m else 'N/A'

    def _extract_address(self, text: str) -> str:
        m = re.search(r'(\d+[,\s][A-Za-z\s]+(?:Street|Ave|Road|Lane|Dr|Blvd|Way)[,\s][A-Za-z\s,]+\d{5,6})', text, re.IGNORECASE)
        return m.group(1).strip() if m else 'N/A'

    def _extract_invitee(self, text: str) -> str:
        m = re.search(r'(?:invite|inviting|request the visa for)\s+(?:mr\.|mrs\.|ms\.)?\s*([A-Z][a-zA-Z\s]{2,40})', text, re.IGNORECASE)
        return m.group(1).strip() if m else 'N/A'

    def _extract_purpose(self, text: str) -> str:
        purposes = ['tourism', 'business', 'medical', 'education', 'family visit', 'wedding', 'conference', 'holiday']
        for p in purposes:
            if p in text.lower():
                return p.title()
        return 'N/A'

    def _extract_duration(self, text: str) -> str:
        m = re.search(r'(?:for|duration of|staying for|period of)\s+(\d+\s+(?:days?|weeks?|months?))', text, re.IGNORECASE)
        return m.group(1) if m else 'N/A'

    def _extract_relationship(self, text: str) -> str:
        relationships = ['friend', 'relative', 'colleague', 'spouse', 'parent', 'sibling', 'brother', 'sister', 'uncle', 'aunt', 'cousin', 'host']
        for r in relationships:
            if r in text.lower():
                return r.title()
        return 'N/A'

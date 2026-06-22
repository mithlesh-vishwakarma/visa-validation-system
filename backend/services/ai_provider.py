"""
AI Provider Abstraction Layer
=============================
This module defines a unified interface for AI document analysis.
Supported providers: mock (default), openai, claude, gemini.

To switch providers, set AI_PROVIDER in your .env:
    AI_PROVIDER=openai    # Requires OPENAI_API_KEY
    AI_PROVIDER=claude    # Requires ANTHROPIC_API_KEY
    AI_PROVIDER=gemini    # Requires GOOGLE_AI_API_KEY
    AI_PROVIDER=mock      # No key needed (default)

All providers implement the same AIProvider interface so they are
fully interchangeable without changing any calling code.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any
from django.conf import settings

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """
    Abstract base class for all AI providers.
    Every concrete provider must implement these two methods.
    """

    @abstractmethod
    def analyze_document(self, doc_category: str, raw_text: str, extracted_data: dict) -> dict:
        """
        Perform AI-powered analysis on a single document.

        Args:
            doc_category: Document slug (e.g., 'passport', 'bank_statement')
            raw_text: Full OCR-extracted text from the document
            extracted_data: Pre-parsed structured data from the OCR service

        Returns:
            dict: Structured AI analysis result for the document type
        """
        pass

    @abstractmethod
    def generate_eligibility_assessment(self, submission_data: dict) -> dict:
        """
        Generate overall eligibility assessment from all document analyses.

        Args:
            submission_data: Dict containing all documents, extracted data,
                            country rules, and cross-validation results

        Returns:
            dict: {strengths, risks, recommendations, summary, eligible}
        """
        pass

    def _build_document_prompt(self, doc_category: str, raw_text: str, extracted_data: dict) -> str:
        """
        Build the analysis prompt for LLMs, including document verification guidelines.
        """
        return (
            f"Analyze this document which is expected to be a '{doc_category.replace('_', ' ')}' for a visa application.\n\n"
            f"Pre-extracted data: {extracted_data}\n\n"
            f"Raw document text (first 2000 chars): {raw_text[:2000]}\n\n"
            f"CRITICAL INSTRUCTIONS:\n"
            f"1. First, check if the raw text matches the expected category '{doc_category}'.\n"
            f"2. If the document is obviously a different type (for example, a School Leaving Certificate, SSC/HSC certificate, marksheet, or passing certificate uploaded instead of a passport or bank statement), you MUST flag this mismatch.\n"
            f"3. In case of mismatch:\n"
            f"   - Set 'invalid_document_type': true\n"
            f"   - Add a detail anomaly in the 'anomalies' list explaining the mismatch (e.g., 'Document Mismatch: Uploaded document is a School Leaving Certificate, not a Passport')\n"
            f"   - Set 'confidence': 0.0\n"
            f"   - Return default empty/zero values for other category-specific fields.\n"
            f"4. If it matches, perform standard extraction. Return a JSON object with document-specific fields, 'anomalies' (list of strings), and 'confidence' (float 0.0-1.0)."
        )



# ---------------------------------------------------------------------------
# OpenAI Provider
# ---------------------------------------------------------------------------

class OpenAIProvider(AIProvider):
    """
    OpenAI GPT-4 provider for production AI analysis.
    Requires OPENAI_API_KEY environment variable.
    """

    def __init__(self):
        try:
            from openai import OpenAI # type: ignore
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
        except ImportError:
            logger.error("openai package not installed.")
            raise

    def analyze_document(self, doc_category: str, raw_text: str, extracted_data: dict) -> dict:
        prompt = self._build_document_prompt(doc_category, raw_text, extracted_data)
        try:
            import json
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert visa document analyst. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            raise

    def generate_eligibility_assessment(self, submission_data: dict) -> dict:
        from services.eligibility_engine import compute_eligibility
        return compute_eligibility(submission_data)


# ---------------------------------------------------------------------------
# Claude (Anthropic) Provider
# ---------------------------------------------------------------------------

class ClaudeProvider(AIProvider):
    """
    Anthropic Claude provider for production AI analysis.
    Requires ANTHROPIC_API_KEY environment variable.
    """

    def __init__(self):
        try:
            import anthropic # type: ignore
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = getattr(settings, 'ANTHROPIC_MODEL', 'claude-3-haiku-20240307')
        except ImportError:
            logger.error("anthropic package not installed.")
            raise

    def analyze_document(self, doc_category: str, raw_text: str, extracted_data: dict) -> dict:
        try:
            import json
            prompt = self._build_document_prompt(doc_category, raw_text, extracted_data)
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return json.loads(message.content[0].text)
        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            raise

    def generate_eligibility_assessment(self, submission_data: dict) -> dict:
        from services.eligibility_engine import compute_eligibility
        return compute_eligibility(submission_data)


# ---------------------------------------------------------------------------
# Gemini Provider
# ---------------------------------------------------------------------------

class GeminiProvider(AIProvider):
    """
    Google Gemini provider for production AI analysis.
    Requires GOOGLE_AI_API_KEY environment variable.
    """

    def __init__(self):
        try:
            import google.generativeai as genai # type: ignore
            genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
            self.model = genai.GenerativeModel(
                getattr(settings, 'GOOGLE_AI_MODEL', 'gemini-2.5-flash')
            )
        except ImportError:
            logger.error("google-generativeai not installed.")
            raise

    def analyze_document(self, doc_category: str, raw_text: str, extracted_data: dict) -> dict:
        try:
            import json
            prompt = self._build_document_prompt(doc_category, raw_text, extracted_data)
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            raise e

    def generate_eligibility_assessment(self, submission_data: dict) -> dict:
        from services.eligibility_engine import compute_eligibility
        return compute_eligibility(submission_data)


# ---------------------------------------------------------------------------
# Provider Factory — returns the configured provider singleton
# ---------------------------------------------------------------------------

_provider_instance: AIProvider | None = None


def get_ai_provider() -> AIProvider:
    """
    Returns the configured AI provider singleton.
    Provider is determined by the AI_PROVIDER environment variable.
    """
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    provider_name = getattr(settings, 'AI_PROVIDER', 'gemini').lower()
    logger.info(f"Initializing AI provider: {provider_name}")

    if provider_name == 'openai' and getattr(settings, 'OPENAI_API_KEY', ''):
        _provider_instance = OpenAIProvider()
    elif provider_name == 'claude' and getattr(settings, 'ANTHROPIC_API_KEY', ''):
        _provider_instance = ClaudeProvider()
    elif provider_name == 'gemini' and getattr(settings, 'GOOGLE_AI_API_KEY', ''):
        _provider_instance = GeminiProvider()
    else:
        raise ValueError(
            f"AI provider '{provider_name}' requested but API key not set or provider invalid. "
            f"Please configure the API keys in your .env file."
        )

    return _provider_instance

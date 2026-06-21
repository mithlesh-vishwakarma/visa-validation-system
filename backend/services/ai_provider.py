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


# ---------------------------------------------------------------------------
# Mock AI Provider (Default — No API Key Required)
# ---------------------------------------------------------------------------

class MockAIProvider(AIProvider):
    """
    Intelligent mock AI provider for development and testing.
    Returns realistic structured analysis based on extracted document data.
    No API key or network connection required.
    """

    def analyze_document(self, doc_category: str, raw_text: str, extracted_data: dict) -> dict:
        """Generate realistic mock analysis per document category."""
        from services.document_analyzers import get_analyzer
        analyzer = get_analyzer(doc_category)
        return analyzer.analyze(raw_text, extracted_data)

    def generate_eligibility_assessment(self, submission_data: dict) -> dict:
        """Generate mock eligibility assessment from scoring engine."""
        from services.eligibility_engine import compute_eligibility
        return compute_eligibility(submission_data)


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
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
        except ImportError:
            logger.warning("openai package not installed. Falling back to mock.")
            self._fallback = MockAIProvider()

    def analyze_document(self, doc_category: str, raw_text: str, extracted_data: dict) -> dict:
        if hasattr(self, '_fallback'):
            return self._fallback.analyze_document(doc_category, raw_text, extracted_data)

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
            logger.error(f"OpenAI analysis failed: {e}. Using mock fallback.")
            return MockAIProvider().analyze_document(doc_category, raw_text, extracted_data)

    def generate_eligibility_assessment(self, submission_data: dict) -> dict:
        if hasattr(self, '_fallback'):
            return self._fallback.generate_eligibility_assessment(submission_data)
        return MockAIProvider().generate_eligibility_assessment(submission_data)

    def _build_document_prompt(self, doc_category: str, raw_text: str, extracted_data: dict) -> str:
        return (
            f"Analyze this {doc_category.replace('_', ' ')} document for a visa application.\n\n"
            f"Pre-extracted data: {extracted_data}\n\n"
            f"Raw document text (first 2000 chars): {raw_text[:2000]}\n\n"
            f"Return a JSON object with document-specific fields and an 'anomalies' list of any suspicious findings."
        )


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
            import anthropic
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = getattr(settings, 'ANTHROPIC_MODEL', 'claude-3-haiku-20240307')
        except ImportError:
            logger.warning("anthropic package not installed. Falling back to mock.")
            self._fallback = MockAIProvider()

    def analyze_document(self, doc_category: str, raw_text: str, extracted_data: dict) -> dict:
        if hasattr(self, '_fallback'):
            return self._fallback.analyze_document(doc_category, raw_text, extracted_data)
        try:
            import json
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Analyze this visa document ({doc_category}). "
                        f"Pre-extracted: {extracted_data}. "
                        f"Text: {raw_text[:2000]}. "
                        f"Respond with JSON only."
                    )
                }]
            )
            return json.loads(message.content[0].text)
        except Exception as e:
            logger.error(f"Claude analysis failed: {e}. Using mock fallback.")
            return MockAIProvider().analyze_document(doc_category, raw_text, extracted_data)

    def generate_eligibility_assessment(self, submission_data: dict) -> dict:
        return MockAIProvider().generate_eligibility_assessment(submission_data)


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
            import google.generativeai as genai
            genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
            self.model = genai.GenerativeModel(
                getattr(settings, 'GOOGLE_AI_MODEL', 'gemini-1.5-flash')
            )
        except ImportError:
            logger.warning("google-generativeai not installed. Falling back to mock.")
            self._fallback = MockAIProvider()

    def analyze_document(self, doc_category: str, raw_text: str, extracted_data: dict) -> dict:
        if hasattr(self, '_fallback'):
            return self._fallback.analyze_document(doc_category, raw_text, extracted_data)
        try:
            import json
            prompt = (
                f"Analyze this visa document ({doc_category}) and return JSON only. "
                f"Pre-extracted data: {extracted_data}. "
                f"Document text: {raw_text[:2000]}"
            )
            response = self.model.generate_content(prompt)
            text = response.text.strip().lstrip('```json').rstrip('```').strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}. Using mock fallback.")
            return MockAIProvider().analyze_document(doc_category, raw_text, extracted_data)

    def generate_eligibility_assessment(self, submission_data: dict) -> dict:
        return MockAIProvider().generate_eligibility_assessment(submission_data)


# ---------------------------------------------------------------------------
# Provider Factory — returns the configured provider singleton
# ---------------------------------------------------------------------------

_provider_instance: AIProvider | None = None


def get_ai_provider() -> AIProvider:
    """
    Returns the configured AI provider singleton.
    Provider is determined by the AI_PROVIDER environment variable.
    Defaults to MockAIProvider if not set or if the configured provider fails.
    """
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    provider_name = getattr(settings, 'AI_PROVIDER', 'mock').lower()
    logger.info(f"Initializing AI provider: {provider_name}")

    if provider_name == 'openai' and getattr(settings, 'OPENAI_API_KEY', ''):
        _provider_instance = OpenAIProvider()
    elif provider_name == 'claude' and getattr(settings, 'ANTHROPIC_API_KEY', ''):
        _provider_instance = ClaudeProvider()
    elif provider_name == 'gemini' and getattr(settings, 'GOOGLE_AI_API_KEY', ''):
        _provider_instance = GeminiProvider()
    else:
        if provider_name != 'mock':
            logger.warning(
                f"AI provider '{provider_name}' requested but API key not set. "
                f"Falling back to MockAIProvider."
            )
        _provider_instance = MockAIProvider()

    return _provider_instance

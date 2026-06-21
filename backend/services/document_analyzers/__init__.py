"""
Document Analyzers Package
===========================
Each analyzer is responsible for performing intelligent structured data
extraction from a specific document type using the OCR raw text and
pre-extracted heuristic data.

Usage:
    from services.document_analyzers import get_analyzer
    analyzer = get_analyzer('passport')
    result = analyzer.analyze(raw_text, extracted_data)
"""

from services.document_analyzers.passport import PassportAnalyzer
from services.document_analyzers.bank_statement import BankStatementAnalyzer
from services.document_analyzers.salary_slip import SalarySlipAnalyzer
from services.document_analyzers.employment_letter import EmploymentLetterAnalyzer
from services.document_analyzers.tax_return import TaxReturnAnalyzer
from services.document_analyzers.travel_history import TravelHistoryAnalyzer
from services.document_analyzers.invitation_letter import InvitationLetterAnalyzer
from services.document_analyzers.hotel_booking import HotelBookingAnalyzer
from services.document_analyzers.flight_booking import FlightBookingAnalyzer
from services.document_analyzers.cover_letter import CoverLetterAnalyzer
from services.document_analyzers.base import BaseAnalyzer

# Registry mapping category slugs to analyzer classes
_ANALYZER_REGISTRY = {
    'passport': PassportAnalyzer,
    'bank_statement': BankStatementAnalyzer,
    'salary_slip': SalarySlipAnalyzer,
    'employment_letter': EmploymentLetterAnalyzer,
    'tax_return': TaxReturnAnalyzer,
    'travel_history': TravelHistoryAnalyzer,
    'invitation_letter': InvitationLetterAnalyzer,
    'hotel_booking': HotelBookingAnalyzer,
    'flight_booking': FlightBookingAnalyzer,
    'cover_letter': CoverLetterAnalyzer,
}


def get_analyzer(doc_category: str) -> BaseAnalyzer:
    """
    Returns the appropriate analyzer instance for a document category slug.
    Falls back to BaseAnalyzer (generic) if category not recognized.

    Args:
        doc_category: Category slug e.g. 'passport', 'bank_statement'

    Returns:
        Concrete analyzer instance
    """
    analyzer_class = _ANALYZER_REGISTRY.get(doc_category.lower(), BaseAnalyzer)
    return analyzer_class()


__all__ = [
    'get_analyzer',
    'PassportAnalyzer',
    'BankStatementAnalyzer',
    'SalarySlipAnalyzer',
    'EmploymentLetterAnalyzer',
    'TaxReturnAnalyzer',
    'TravelHistoryAnalyzer',
    'InvitationLetterAnalyzer',
    'HotelBookingAnalyzer',
    'FlightBookingAnalyzer',
    'CoverLetterAnalyzer',
    'BaseAnalyzer',
]

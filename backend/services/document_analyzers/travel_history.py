"""Travel History Analyzer — extracts countries visited, visa history, and travel frequency."""

import re
from services.document_analyzers.base import BaseAnalyzer


# Known country names for pattern matching
KNOWN_COUNTRIES = [
    'United States', 'USA', 'United Kingdom', 'UK', 'Canada', 'Australia',
    'Germany', 'France', 'Italy', 'Spain', 'Japan', 'Singapore', 'UAE',
    'Dubai', 'Thailand', 'Malaysia', 'Switzerland', 'Netherlands', 'Belgium',
    'New Zealand', 'South Korea', 'China', 'Hong Kong', 'Saudi Arabia',
    'Maldives', 'Sri Lanka', 'Nepal', 'Bangladesh', 'Indonesia', 'Philippines',
    'Portugal', 'Greece', 'Turkey', 'Czech Republic', 'Austria', 'Poland',
    'Sweden', 'Norway', 'Denmark', 'Finland', 'Ireland', 'Scotland',
]

SCHENGEN_COUNTRIES = [
    'Germany', 'France', 'Italy', 'Spain', 'Netherlands', 'Belgium',
    'Austria', 'Greece', 'Portugal', 'Czech Republic', 'Poland', 'Sweden',
    'Norway', 'Denmark', 'Finland', 'Switzerland',
]


class TravelHistoryAnalyzer(BaseAnalyzer):
    def analyze(self, raw_text: str, extracted_data: dict) -> dict:
        text = raw_text or ''

        countries_visited = self._extract_countries(text)
        schengen_visits = [c for c in countries_visited if c in SCHENGEN_COUNTRIES]
        western_country_visits = [c for c in countries_visited if c in ['USA', 'United States', 'UK', 'United Kingdom', 'Canada', 'Australia', 'New Zealand']]

        travel_count = len(countries_visited)
        visa_stamps = self._count_visa_stamps(text)
        travel_frequency = self._classify_frequency(travel_count)

        # Extract dates of travel
        has_recent_travel = self._has_recent_travel(text)
        has_visa_rejections = any(kw in text.lower() for kw in ['rejected', 'refused', 'denial', 'not granted'])

        anomalies = self.detect_anomalies([
            (travel_count == 0, "No international travel history found"),
            (has_visa_rejections, "Previous visa rejection detected in travel history"),
            (travel_count < 2, "Limited travel history — fewer than 2 countries visited"),
        ])

        # Travel score (0–100)
        travel_score = self._compute_travel_score(travel_count, schengen_visits, western_country_visits, has_visa_rejections)

        return {
            "document_type": "travel_history",
            "countries_visited": countries_visited,
            "total_countries_count": travel_count,
            "schengen_visits": schengen_visits,
            "western_country_visits": western_country_visits,
            "visa_stamps_count": visa_stamps,
            "travel_frequency": travel_frequency,
            "has_recent_travel_last_2_years": has_recent_travel,
            "has_visa_rejections": has_visa_rejections,
            "travel_history_score": travel_score,
            "anomalies": anomalies,
            "confidence": 0.75 if travel_count > 0 else 0.35,
        }

    def _extract_countries(self, text: str) -> list:
        found = []
        for country in KNOWN_COUNTRIES:
            if country.lower() in text.lower() and country not in found:
                found.append(country)
        return found

    def _count_visa_stamps(self, text: str) -> int:
        matches = re.findall(r'(?:stamp|visa|entry|arrival|departure)', text, re.IGNORECASE)
        return len(matches)

    def _has_recent_travel(self, text: str) -> bool:
        recent_years = ['2023', '2024', '2025', '2026']
        return any(yr in text for yr in recent_years)

    def _classify_frequency(self, count: int) -> str:
        if count >= 10:
            return 'Frequent Traveler'
        elif count >= 5:
            return 'Regular Traveler'
        elif count >= 2:
            return 'Occasional Traveler'
        elif count == 1:
            return 'Rare Traveler'
        return 'No History'

    def _compute_travel_score(self, count: int, schengen: list, western: list, has_rejection: bool) -> int:
        score = 40  # Base
        score += min(count * 5, 30)  # Up to 30 pts for country count
        score += min(len(schengen) * 4, 15)  # Schengen bonus
        score += min(len(western) * 5, 15)  # Western country bonus
        if has_rejection:
            score -= 30
        return max(0, min(100, score))

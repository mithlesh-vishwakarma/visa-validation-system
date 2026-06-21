"""Flight Booking / Reservation Analyzer."""

import re
from services.document_analyzers.base import BaseAnalyzer


class FlightBookingAnalyzer(BaseAnalyzer):
    def analyze(self, raw_text: str, extracted_data: dict) -> dict:
        text = raw_text or ''

        passenger_name = self._extract_passenger(text)
        airline = self._extract_airline(text)
        flight_number = self._extract_flight_number(text)
        pnr = self._extract_pnr(text)

        departure_date = self.extract_date(text, ['departure', 'departs', 'outbound', 'from'])
        return_date = self.extract_date(text, ['return', 'inbound', 'arrives back', 'arrival'])

        origin = self._extract_airport(text, 'origin')
        destination = self._extract_airport(text, 'destination')

        is_return_ticket = return_date is not None or 'return' in text.lower()
        booking_class = self._extract_class(text)

        anomalies = self.detect_anomalies([
            (not pnr, "PNR / booking reference not found"),
            (not departure_date, "Departure date missing from itinerary"),
            (not is_return_ticket, "One-way ticket only — return ticket often required for visa"),
            (not airline or airline == 'N/A', "Airline name not identified"),
        ])

        return {
            "document_type": "flight_booking",
            "passenger_name": passenger_name,
            "airline": airline,
            "flight_number": flight_number,
            "pnr_reference": pnr,
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "is_return_ticket": is_return_ticket,
            "booking_class": booking_class,
            "anomalies": anomalies,
            "confidence": 0.80 if pnr and departure_date else 0.45,
        }

    def _extract_passenger(self, text: str) -> str:
        m = re.search(r'(?:passenger|name|traveller)\s*[:\-]?\s*([A-Z][A-Z\s/]{2,40})', text, re.IGNORECASE)
        return m.group(1).strip().title() if m else 'N/A'

    def _extract_airline(self, text: str) -> str:
        airlines = ['Air India', 'IndiGo', 'SpiceJet', 'GoAir', 'Vistara', 'Emirates', 'Etihad',
                    'Qatar Airways', 'British Airways', 'Lufthansa', 'Singapore Airlines', 'Air France',
                    'KLM', 'Swiss', 'Turkish Airlines', 'American Airlines', 'United Airlines',
                    'Delta', 'Air Canada', 'Qantas', 'Cathay Pacific', 'Japan Airlines', 'ANA']
        for airline in airlines:
            if airline.lower() in text.lower():
                return airline
        m = re.search(r'([A-Z][a-zA-Z\s]{2,30}(?:Airlines?|Airways|Air\s[A-Z][a-z]+))', text)
        return m.group(1).strip() if m else 'N/A'

    def _extract_flight_number(self, text: str) -> str:
        m = re.search(r'\b([A-Z]{2,3}[\s\-]?\d{2,4})\b', text)
        return m.group(1) if m else 'N/A'

    def _extract_pnr(self, text: str) -> str:
        m = re.search(r'(?:PNR|booking\s+ref|confirmation)\s*[:\-]?\s*([A-Z0-9]{6,10})', text, re.IGNORECASE)
        return m.group(1) if m else None

    def _extract_airport(self, text: str, which: str) -> str:
        if which == 'origin':
            m = re.search(r'(?:from|origin|departure\s+city)\s*[:\-]?\s*([A-Z][a-zA-Z\s]{2,30})', text, re.IGNORECASE)
        else:
            m = re.search(r'(?:to|destination|arrival\s+city)\s*[:\-]?\s*([A-Z][a-zA-Z\s]{2,30})', text, re.IGNORECASE)
        return m.group(1).strip() if m else 'N/A'

    def _extract_class(self, text: str) -> str:
        if any(kw in text.lower() for kw in ['business class', 'business']):
            return 'Business'
        elif any(kw in text.lower() for kw in ['first class', 'first']):
            return 'First'
        return 'Economy'

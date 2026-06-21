"""Hotel Booking Analyzer."""

import re
from services.document_analyzers.base import BaseAnalyzer


class HotelBookingAnalyzer(BaseAnalyzer):
    def analyze(self, raw_text: str, extracted_data: dict) -> dict:
        text = raw_text or ''
        hotel_name = self._extract_hotel(text)
        guest_name = self._extract_guest(text)
        check_in = self.extract_date(text, ['check-in', 'check in', 'arrival', 'from'])
        check_out = self.extract_date(text, ['check-out', 'check out', 'departure', 'to'])
        booking_ref = self._extract_booking_ref(text)
        total_cost = self.extract_amount(text, ['total', 'amount', 'cost', 'charges'], 0.0)
        destination = self._extract_destination(text)
        is_confirmed = any(kw in text.lower() for kw in ['confirmed', 'reservation confirmed', 'booking confirmed'])

        anomalies = self.detect_anomalies([
            (not hotel_name or hotel_name == 'N/A', "Hotel name not identified"),
            (not check_in, "Check-in date missing from booking"),
            (not check_out, "Check-out date missing from booking"),
            (not is_confirmed, "Booking confirmation status unclear"),
        ])

        return {
            "document_type": "hotel_booking",
            "hotel_name": hotel_name,
            "guest_name": guest_name,
            "destination": destination,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "booking_reference": booking_ref,
            "total_cost": round(total_cost, 2),
            "is_confirmed": is_confirmed,
            "anomalies": anomalies,
            "confidence": 0.75 if hotel_name != 'N/A' and check_in else 0.40,
        }

    def _extract_hotel(self, text: str) -> str:
        m = re.search(r'([A-Z][a-zA-Z\s]{2,40}(?:Hotel|Resort|Inn|Suites|Lodge|Marriott|Hilton|Hyatt|Sheraton|ITC|Taj|Oberoi))', text, re.IGNORECASE)
        return m.group(1).strip() if m else 'N/A'

    def _extract_guest(self, text: str) -> str:
        m = re.search(r'(?:guest name|booked for|guest)\s*[:\-]?\s*([A-Z][a-zA-Z\s]{2,40})', text, re.IGNORECASE)
        return m.group(1).strip() if m else 'N/A'

    def _extract_booking_ref(self, text: str) -> str:
        m = re.search(r'(?:booking|reservation|confirmation|ref(?:erence)?)\s*(?:no\.?|#|id)?\s*[:\-]?\s*([A-Z0-9]{5,15})', text, re.IGNORECASE)
        return m.group(1) if m else 'N/A'

    def _extract_destination(self, text: str) -> str:
        m = re.search(r'(?:located in|location|city|at)\s*[:\-]?\s*([A-Z][a-zA-Z\s]{2,30})', text, re.IGNORECASE)
        return m.group(1).strip() if m else 'N/A'

"""
nagarAI - shared/complaint_schema.py
====================================
Defines the Complaint dataclass and helper classes for geocoding and triage.
"""

import dataclasses
from typing import Optional

@dataclasses.dataclass
class Complaint:
    source_modality: str
    category: str
    description: str
    location_mention: Optional[str]
    gps_lat: Optional[float]
    gps_lng: Optional[float]
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    geocoded_lat: Optional[float] = None
    geocoded_lng: Optional[float] = None
    severity: Optional[int] = None
    people_affected: Optional[int] = None


class Geocoder:
    def __init__(self):
        # Could wrap Google Maps, Mapbox, or OpenStreetMap Nominatim
        pass

    def geocode(self, location_text: str):
        """
        Dummy geocode implementation. Replace with real API call.
        Returns (lat, lng) or None.
        """
        # Example: return (13.0475, 80.2500) if location_text == "Thiruvanmiyur"
        return None

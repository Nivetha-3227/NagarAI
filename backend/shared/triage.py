import math
from typing import List, Optional

class TriageEstimator:
    def __init__(self):
        pass

    def haversine(self, lat1, lon1, lat2, lon2):
        """Calculate haversine distance in km between two GPS points."""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2)**2 +
             math.cos(math.radians(lat1)) *
             math.cos(math.radians(lat2)) *
             math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def estimate(self,
                 complaints: List[dict],
                 gps_lat: float,
                 gps_lng: float,
                 nearby_places: Optional[List[dict]] = None):
        """
        complaints: list of complaint dicts (voice/text/image results)
        gps_lat/gps_lng: location of merged complaint
        nearby_places: list of sensitive places (schools/hospitals) with lat/lng
        """

        # Count people affected
        people_affected = len(complaints)

        # Check clustering (within 1 km)
        clustered = 0
        for c in complaints:
            if c.get("gps_lat") and c.get("gps_lng"):
                dist = self.haversine(gps_lat, gps_lng, c["gps_lat"], c["gps_lng"])
                if dist < 1.0:
                    clustered += 1
        people_affected = max(people_affected, clustered)

        # Check sensitive zones
        high_priority_zone = False
        if nearby_places:
            for place in nearby_places:
                dist = self.haversine(gps_lat, gps_lng, place["lat"], place["lng"])
                if dist < 0.5:  # within 500m
                    high_priority_zone = True
                    break

        # Assign severity
        if high_priority_zone:
            severity = 5
        elif people_affected > 10:
            severity = 5
        elif people_affected >= 8:
            severity = 4
        elif people_affected >= 6:
            severity = 3
        elif people_affected >= 4:
            severity = 2
        else:
            severity = 1

        return severity, people_affected

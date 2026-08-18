"""
nagarAI - shared/supabase_client.py
===================================
Wrapper for Supabase operations: uploading files and inserting complaints.
"""

import os
from supabase import create_client, Client
from backend.database import supabase
class SupabaseComplaintStore:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.client: Client = create_client(url, key)

    def upload_audio(self, audio_path: str) -> str:
        """Uploads audio file to Supabase storage and returns URL."""
        bucket = "complaints"
        with open(audio_path, "rb") as f:
            self.client.storage.from_(bucket).upload(audio_path, f)
        return f"{bucket}/{audio_path}"

    def upload_image(self, image_path: str) -> str:
        """Uploads image file to Supabase storage and returns URL."""
        bucket = "complaints"
        with open(image_path, "rb") as f:
            self.client.storage.from_(bucket).upload(image_path, f)
        return f"{bucket}/{image_path}"

    def insert_complaint(self, complaint) -> dict:
        """Insert complaint dataclass into Supabase table."""
        row = {
            "source_modality": complaint.source_modality,
            "category": complaint.category,
            "description": complaint.description,
            "location_mention": complaint.location_mention,
            "gps_lat": complaint.gps_lat,
            "gps_lng": complaint.gps_lng,
            "audio_url": complaint.audio_url,
            "image_url": complaint.image_url,
            "geocoded_lat": complaint.geocoded_lat,
            "geocoded_lng": complaint.geocoded_lng,
            "severity": complaint.severity,
            "people_affected": complaint.people_affected,
            "status": "Pending",
        }
        clean_row = {k: v for k, v in row.items() if v is not None}
        response = self.client.table("complaints").insert(clean_row).execute()
        return response.data

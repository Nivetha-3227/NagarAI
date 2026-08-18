import os
import tempfile
from groq import Groq


class VoiceComplaintPipeline:
    def __init__(self):
        self.client = Groq()  # reads GROQ_API_KEY from env

    def process(self, audio_path, gps_lat=None, gps_lng=None):
        with open(audio_path, "rb") as f:
            translation = self.client.audio.translations.create(
                file=(os.path.basename(audio_path), f.read()),
                model="whisper-large-v3",
            )
        transcript = translation.text.strip()

        extraction = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            messages=[{
                "role": "user",
                "content": f'''Extract structured data from this civic complaint transcript.
Return ONLY raw JSON, no markdown fences:
{{"category": "pothole|garbage|streetlight|waterlogging|other", "location_mention": "<mentioned place or null>", "description": "<one clean sentence>"}}

Transcript: """{transcript}"""'''
            }],
        )
        import json, re
        raw = extraction.choices[0].message.content.strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        fields = json.loads(match.group(0) if match else raw)

        return {
            "category": fields.get("category", "other"),
            "location_mention": fields.get("location_mention"),
            "description": fields.get("description", transcript[:150]),
            "raw_transcript": transcript,
            "gps_lat": gps_lat,
            "gps_lng": gps_lng,
        }

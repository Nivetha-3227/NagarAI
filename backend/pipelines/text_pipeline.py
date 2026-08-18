import uuid, datetime, dataclasses
from typing import Optional
from backend.database import supabase
from shared.nlp import CategoryClassifier, Summarizer

@dataclasses.dataclass
class TextComplaintResult:
    complaint_id: str
    category: str
    category_confidence: float
    description: str
    location_mention: Optional[str]
    gps_lat: Optional[float]
    gps_lng: Optional[float]
    raw_text: str
    created_at: str

class TextComplaintPipeline:
    def __init__(self):
        self.classifier = CategoryClassifier()
        self.summarizer = Summarizer()

    def process(self, text: str, gps_lat: Optional[float]=None, gps_lng: Optional[float]=None) -> TextComplaintResult:
        category, confidence = self.classifier.classify(text)
        summary = self.summarizer.summarize(text, category)
        return TextComplaintResult(
            complaint_id=str(uuid.uuid4()),
            category=category,
            category_confidence=round(confidence, 3),
            description=summary,
            location_mention=None,  # optional: run location extractor if needed
            gps_lat=gps_lat,
            gps_lng=gps_lng,
            raw_text=text,
            created_at=datetime.datetime.utcnow().isoformat(),
        )

def store_text_complaint(result: TextComplaintResult):
    row = {
        "source_modality": "text",
        "category": result.category,
        "description": result.description,
        "location_mention": result.location_mention,
        "gps_lat": result.gps_lat,
        "gps_lng": result.gps_lng,
        "status": "Pending",
        "created_at": result.created_at
    }
    clean_row = {k: v for k, v in row.items() if v is not None}
    return supabase.table("complaints").insert(clean_row).execute()

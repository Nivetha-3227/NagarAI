import uuid, datetime, dataclasses
from typing import Optional
from backend.database import supabase
from backend.shared.nlp import CategoryClassifier, Summarizer


@dataclasses.dataclass
class ImageComplaintResult:
    complaint_id: str
    category: str
    category_confidence: float
    description: str
    location_mention: Optional[str]
    gps_lat: Optional[float]
    gps_lng: Optional[float]
    raw_caption: str
    image_path: str
    created_at: str

class ImageComplaintPipeline:
    def __init__(self):
        self.classifier = CategoryClassifier()
        self.summarizer = Summarizer()

    def process(self, image_path: str, caption: str, gps_lat: Optional[float]=None, gps_lng: Optional[float]=None) -> ImageComplaintResult:
        # caption could come from OCR or a vision model
        category, confidence = self.classifier.classify(caption)
        summary = self.summarizer.summarize(caption, category)
        return ImageComplaintResult(
            complaint_id=str(uuid.uuid4()),
            category=category,
            category_confidence=round(confidence, 3),
            description=summary,
            location_mention=None,
            gps_lat=gps_lat,
            gps_lng=gps_lng,
            raw_caption=caption,
            image_path=image_path,
            created_at=datetime.datetime.utcnow().isoformat(),
        )

def store_image_complaint(result: ImageComplaintResult):
    row = {
        "source_modality": "image",
        "category": result.category,
        "description": result.description,
        "location_mention": result.location_mention,
        "gps_lat": result.gps_lat,
        "gps_lng": result.gps_lng,
        "image_url": result.image_path,
        "status": "Pending",
        "created_at": result.created_at
    }
    clean_row = {k: v for k, v in row.items() if v is not None}
    return supabase.table("complaints").insert(clean_row).execute()

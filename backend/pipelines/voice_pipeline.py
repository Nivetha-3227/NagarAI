import os
import uuid
import datetime
import dataclasses
from typing import Optional, Tuple

# Import your Supabase client setup (adjust path if needed)
from backend.database import supabase

CATEGORIES = [
    "Roads & Traffic",
    "Water & Drainage",
    "Waste Management",
    "Street Lighting & Electricity",
    "Infrastructure Damage",
    "Public Safety",
    "Public Health & Sanitation",
    "Public Transport",
    "Other / General",
]

CATEGORY_DESCRIPTIONS = {
    "Roads & Traffic": "potholes, broken roads, traffic signals not working, traffic jams, illegal parking, road accidents, speed breakers",
    "Water & Drainage": "water supply issues, drainage overflow, sewage leakage, blocked drains, water pipeline leakage, contaminated water",
    "Waste Management": "garbage not collected, overflowing dustbins, illegal dumping, waste segregation issues, dead animals not removed",
    "Street Lighting & Electricity": "street lights not working, power outage, exposed electrical wires, transformer issues, streetlight damaged",
    "Infrastructure Damage": "damaged public property, broken footpaths, collapsed walls, damaged bridges, construction debris left unattended",
    "Public Safety": "unsafe areas, open manholes, stray animals causing danger, unsafe construction sites, lack of security",
    "Public Health & Sanitation": "unhygienic public toilets, mosquito breeding, unsanitary conditions, disease outbreak risk",
    "Public Transport": "bus delays, auto/taxi overcharging, bus stop issues, unavailability of public transport, poor transport infrastructure",
    "Other / General": "general civic complaints not covered elsewhere",
}


@dataclasses.dataclass
class VoiceComplaintResult:
    complaint_id: str
    category: str
    category_confidence: float
    description: str
    location_mention: Optional[str]
    gps_lat: Optional[float]
    gps_lng: Optional[float]
    raw_transcript: str
    detected_language: str
    english_transcript: str
    audio_path: str
    created_at: str


class AudioPreprocessor:
    def __init__(self, low_freq: float = 300.0, high_freq: float = 3400.0, order: int = 5):
        self.low_freq = low_freq
        self.high_freq = high_freq
        self.order = order

    def _butter_bandpass(self, sample_rate: int):
        from scipy.signal import butter
        nyquist = 0.5 * sample_rate
        low = self.low_freq / nyquist
        high = self.high_freq / nyquist
        high = min(high, 0.99)
        return butter(self.order, [low, high], btype="band")

    def filter_file(self, in_path: str, out_path: Optional[str] = None) -> str:
        import librosa
        import soundfile as sf

        audio, sr = librosa.load(in_path, sr=None, mono=True)
        from scipy.signal import filtfilt
        b, a = self._butter_bandpass(sr)
        filtered = filtfilt(b, a, audio)

        if out_path is None:
            out_path = f"/tmp/filtered_{uuid.uuid4().hex}.wav"
        sf.write(out_path, filtered, sr)
        return out_path


class WhisperTranscriber:
    def __init__(self, model_size: str = "large-v3", device: str = "cuda"):
        import whisper
        self.model = whisper.load_model(model_size, device=device)

    def transcribe_native(self, audio_path: str) -> Tuple[str, str]:
        result = self.model.transcribe(audio_path, task="transcribe")
        return result["text"].strip(), result["language"]

    def transcribe_and_translate(self, audio_path: str) -> str:
        result = self.model.transcribe(audio_path, task="translate")
        return result["text"].strip()


class CategoryClassifier:
    def __init__(self, model_name: str = "paraphrase-multilingual-mpnet-base-v2"):
        from sentence_transformers import SentenceTransformer, util
        self.model = SentenceTransformer(model_name)
        self.util = util
        self.category_names = list(CATEGORY_DESCRIPTIONS.keys())
        self.category_embeddings = self.model.encode(
            list(CATEGORY_DESCRIPTIONS.values()), convert_to_tensor=True
        )

    def classify(self, text: str) -> Tuple[str, float]:
        query_embedding = self.model.encode(text, convert_to_tensor=True)
        scores = self.util.cos_sim(query_embedding, self.category_embeddings)[0]
        best_idx = int(scores.argmax())
        return self.category_names[best_idx], float(scores[best_idx])


class Summarizer:
    def summarize(self, english_text: str, category: str) -> str:
        if len(english_text.split()) < 25:
            return english_text.strip()
        from transformers import pipeline
        pipe = pipeline("summarization", model="facebook/bart-large-cnn")
        result = pipe(english_text, max_length=40, min_length=8, do_sample=False)
        return result[0]["summary_text"].strip()


class LocationExtractor:
    def __init__(self, api_key: Optional[str] = None):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)

    def extract(self, text: str) -> Optional[str]:
        try:
            msg = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=50,
                messages=[{
                    "role": "user",
                    "content": (
                        "Extract the specific place/landmark mentioned in this civic "
                        "complaint, if any (e.g. street name, bus stop, area, junction). "
                        "Reply with ONLY the location phrase, or the single word NONE "
                        f"if no location is mentioned.\n\nComplaint: {text}"
                    ),
                }],
            )
            result = msg.content[0].text.strip()
            return None if result.upper() == "NONE" else result
        except Exception:
            return None


class VoiceComplaintPipeline:
    def __init__(self, anthropic_api_key: Optional[str] = None):
        self.preprocessor = AudioPreprocessor()
        self.asr = WhisperTranscriber(model_size="large-v3")
        self.classifier = CategoryClassifier()
        self.summarizer = Summarizer()
        self.location_extractor = LocationExtractor(api_key=anthropic_api_key)

    def process(
        self,
        audio_path: str,
        gps_lat: Optional[float] = None,
        gps_lng: Optional[float] = None,
    ) -> VoiceComplaintResult:
        filtered_path = self.preprocessor.filter_file(audio_path)
        native_text, lang = self.asr.transcribe_native(filtered_path)
        english_text = (
            native_text if lang == "en"
            else self.asr.transcribe_and_translate(filtered_path)
        )

        category, confidence = self.classifier.classify(english_text)
        summary = self.summarizer.summarize(english_text, category)
        location_mention = self.location_extractor.extract(english_text)

        return VoiceComplaintResult(
            complaint_id=str(uuid.uuid4()),
            category=category,
            category_confidence=round(confidence, 3),
            description=summary,
            location_mention=location_mention,
            gps_lat=gps_lat,
            gps_lng=gps_lng,
            raw_transcript=native_text,
            detected_language=lang,
            english_transcript=english_text,
            audio_path=audio_path,
            created_at=datetime.datetime.utcnow().isoformat(),
        )


def store_complaint_in_supabase(result: VoiceComplaintResult, storage_path: Optional[str] = None):
    """Inserts the extracted fields directly into the Supabase complaints table."""
    try:
        row = {
            "source_modality": "voice",
            "category": result.category,
            "description": result.description,
            "location_mention": result.location_mention,
            "gps_lat": result.gps_lat,
            "gps_lng": result.gps_lng,
            "audio_url": storage_path,
            "status": "Pending",
            "created_at": result.created_at
        }
        
        # Drop None fields so database defaults can apply cleanly
        clean_row = {k: v for k, v in row.items() if v is not None}
        
        response = supabase.table("complaints").insert(clean_row).execute()
        print("Successfully stored voice complaint in Supabase:", response.data)
        return response.data
    except Exception as e:
        print(f"Failed to insert into Supabase: {e}")
        return None


if __name__ == "__main__":
    pipeline = VoiceComplaintPipeline()
    audio_path = "sample_complaint.wav"
    
    # Process audio and extract fields
    result = pipeline.process(audio_path, gps_lat=13.0475, gps_lng=80.2500)
    
    # Store directly into Supabase
    store_complaint_in_supabase(result, storage_path="voice/sample_complaint.wav")

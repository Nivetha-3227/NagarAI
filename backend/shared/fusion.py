"""
nagarAI - shared/fusion.py
=============================
Fusion logic: combines results from voice, text, and/or image complaints
into one unified Complaint record, enriches with geocoding + triage,
and stores in Supabase.
"""

from typing import Optional, List
from shared.complaint_schema import Complaint, Geocoder, TriageEstimator
from shared.supabase_client import SupabaseComplaintStore

# Import Gemini client
from google import genai


def _merge_category(results: List[dict]) -> str:
    from collections import Counter
    votes = Counter(r["category"] for r in results)
    top_count = votes.most_common(1)[0][1]
    tied = [cat for cat, count in votes.items() if count == top_count]
    if len(tied) == 1:
        return tied[0]
    # break ties by highest confidence among the tied categories
    best = max((r for r in results if r["category"] in tied),
               key=lambda r: r["category_confidence"])
    return best["category"]


def _merge_location(results: List[dict]) -> Optional[str]:
    mentions = [r.get("location_mention") for r in results if r.get("location_mention")]
    return max(mentions, key=len) if mentions else None


def _merge_gps(results: List[dict]) -> tuple:
    for r in results:
        if r.get("gps_lat") is not None and r.get("gps_lng") is not None:
            return r["gps_lat"], r["gps_lng"]
    return None, None


def _merge_description(results: List[dict], category: str, api_key: Optional[str] = None) -> str:
    if len(results) == 1:
        return results[0]["description"]

    client = genai.Client(api_key=api_key)
    combined_input = "\n".join(f"- ({r['source']}): {r['description']}" for r in results)

    prompt = (
        f"These are separate descriptions of the SAME civic complaint "
        f"(category: {category}), captured via different input methods. "
        f"Combine them into one coherent sentence (max 30 words), keeping "
        f"any concrete detail (location, severity) mentioned in any of them:\n\n{combined_input}"
    )

    response = client.generate_text(model="gemini-1.5-flash", prompt=prompt)
    return response.text.strip()


def fuse_and_submit(
    voice_result=None,   # VoiceComplaintResult or None
    text_result=None,    # TextComplaintResult or None
    image_result=None,   # ImageComplaintResult or None
    audio_path: Optional[str] = None,
    image_path: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
) -> dict:
    """Call after running whichever of the 3 pipelines apply. Returns the inserted row."""

    results = []
    if voice_result:
        results.append({"source": "voice", "category": voice_result.category,
                         "category_confidence": voice_result.category_confidence,
                         "description": voice_result.description,
                         "location_mention": voice_result.location_mention,
                         "gps_lat": voice_result.gps_lat, "gps_lng": voice_result.gps_lng})
    if text_result:
        results.append({"source": "text", "category": text_result.category,
                         "category_confidence": text_result.category_confidence,
                         "description": text_result.description,
                         "location_mention": text_result.location_mention,
                         "gps_lat": text_result.gps_lat, "gps_lng": text_result.gps_lng})
    if image_result:
        results.append({"source": "image", "category": image_result.category,
                         "category_confidence": image_result.category_confidence,
                         "description": image_result.description,
                         "location_mention": image_result.location_mention,
                         "gps_lat": image_result.gps_lat, "gps_lng": image_result.gps_lng})

    if not results:
        raise ValueError("At least one of voice_result/text_result/image_result is required")

    category = _merge_category(results)
    description = _merge_description(results, category, api_key=gemini_api_key)
    location_mention = _merge_location(results)
    gps_lat, gps_lng = _merge_gps(results)
    source_modality = "+".join(r["source"] for r in results)

    store = SupabaseComplaintStore()
    audio_url = store.upload_audio(audio_path) if audio_path else None
    image_url = store.upload_image(image_path) if image_path else None

    complaint = Complaint(
        source_modality=source_modality,
        category=category,
        description=description,
        location_mention=location_mention,
        gps_lat=gps_lat,
        gps_lng=gps_lng,
        audio_url=audio_url,
        image_url=image_url,
    )

    # cross-modality enrichment -- geocode the merged location, estimate triage
    geocoder = Geocoder()
    if complaint.location_mention:
        coords = geocoder.geocode(complaint.location_mention)
        if coords:
            complaint.geocoded_lat, complaint.geocoded_lng = coords

    triage = TriageEstimator(api_key=gemini_api_key)
    complaint.severity, complaint.people_affected = triage.estimate(
        complaint.description, complaint.category
    )

    return store.insert_complaint(complaint)

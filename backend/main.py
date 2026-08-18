from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from backend.pipelines.voice_pipeline import VoiceComplaintPipeline, store_complaint_in_supabase
from backend.pipelines.text_pipeline import TextComplaintPipeline, store_text_complaint
from backend.pipelines.image_pipeline import ImageComplaintPipeline, store_image_complaint

app = FastAPI(title="nagarAI Civic Complaint API")

# ============================================================
# CORS MIDDLEWARE CONFIGURATION
# ============================================================
# This explicitly allows your GitHub Pages frontend domains to talk to this backend
origins = [
    "https://nivetha-3227.github.io",
    "https://sheril07.github.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows any origin, including all GitHub pages domains
    allow_credentials=False,  # Note: Must be False if allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)
from fastapi import Response

@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str, response: Response):
    response.headers["Access-Control-Allow-Origin"] = "https://nivetha-3227.github.io"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response
# ============================================================
# 1. VOICE COMPLAINT ENDPOINTS
# ============================================================
# Aligned route to match script.js fetch pathway: ${API_BASE_URL}/complaints/voice
@app.post("/complaints/voice")
async def submit_voice(
    audio: UploadFile, 
    gps_lat: float = Form(None), 
    gps_lng: float = Form(None)
):
    pipeline = VoiceComplaintPipeline()
    result = pipeline.process(audio.file.name, gps_lat=gps_lat, gps_lng=gps_lng)
    return store_complaint_in_supabase(result, storage_path=audio.filename)


# ============================================================
# 2. TEXT COMPLAINT ENDPOINTS
# ============================================================
# Aligned route to match script.js fetch pathway: ${API_BASE_URL}/api/text-intake
# Changed parameters from Form(...) to accept the incoming frontend JSON object directly
@app.post("/api/text-intake")
async def submit_text(payload: dict):
    # Extract data from the incoming JSON body structured by script.js
    text = payload.get("text", "")
    gps_lat = payload.get("gps_lat")
    gps_lng = payload.get("gps_lng")
    
    pipeline = TextComplaintPipeline()
    result = pipeline.process(text, gps_lat=gps_lat, gps_lng=gps_lng)
    return store_text_complaint(result)


# ============================================================
# 3. IMAGE COMPLAINT ENDPOINTS
# ============================================================
@app.post("/complaint/image")
async def submit_image(
    image: UploadFile, 
    caption: str = Form(...), 
    gps_lat: float = Form(None), 
    gps_lng: float = Form(None)
):
    pipeline = ImageComplaintPipeline()
    result = pipeline.process(image.file.name, caption, gps_lat=gps_lat, gps_lng=gps_lng)
    return store_image_complaint(result)

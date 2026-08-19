import os
import tempfile
import traceback

from fastapi import FastAPI, UploadFile, Form, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import your custom pipeline modules
try:
    from backend.pipelines.voice_pipeline import VoiceComplaintPipeline, store_complaint_in_supabase
    from backend.pipelines.text_pipeline import TextComplaintPipeline, store_text_complaint
    from backend.pipelines.image_pipeline import ImageComplaintPipeline, store_image_complaint
except Exception as import_error:
    print(f"Import Error detected during boot: {str(import_error)}")

app = FastAPI(title="nagarAI Civic Complaint API")

# ============================================================
# 1. CORS MIDDLEWARE SETUP
# ============================================================
origins = [
    "https://nivetha-3227.github.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 2. BULLETPROOF CORS EXCEPTION HANDLER
# ============================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_trace = traceback.format_exc()
    print(f"CRASH LOG:\n{error_trace}")  # Appears in your Render Terminal Logs

    origin = request.headers.get("origin", "")
    allowed_origin = origin if origin in origins else origins[0]

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Backend Pipeline Crash",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": error_trace
        },
        headers={
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# ============================================================
# 3. DIAGNOSTIC CONNECTION TEST ROUTE
# ============================================================
@app.get("/api/test-connection")
async def test_connection():
    return {"status": "success", "message": "CORS handshake is perfectly functional!"}

# ============================================================
# 4. COMPLAINT INTAKE PATHWAYS
# ============================================================
@app.post("/complaint/voice")
async def submit_voice(
    audio: UploadFile,
    gps_lat: float = Form(None),
    gps_lng: float = Form(None)
):
    audio_bytes = await audio.read()
    suffix = os.path.splitext(audio.filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    pipeline = VoiceComplaintPipeline()
    try:
        result = pipeline.process(tmp_path, gps_lat=gps_lat, gps_lng=gps_lng)
    finally:
        os.remove(tmp_path)

    return store_complaint_in_supabase(result, storage_path=audio.filename)


@app.post("/complaint/text")
async def submit_text(payload: dict):
    text = payload.get("text", "")
    gps_lat = payload.get("gps_lat")
    gps_lng = payload.get("gps_lng")

    pipeline = TextComplaintPipeline()
    result = pipeline.process(text, gps_lat=gps_lat, gps_lng=gps_lng)
    return store_text_complaint(result)


@app.post("/complaint/image")
async def submit_image(
    image: UploadFile,
    caption: str = Form(...),
    gps_lat: float = Form(None),
    gps_lng: float = Form(None)
):
    image_bytes = await image.read()
    suffix = os.path.splitext(image.filename)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    pipeline = ImageComplaintPipeline()
    try:
        result = pipeline.process(tmp_path, caption, gps_lat=gps_lat, gps_lng=gps_lng)
    finally:
        os.remove(tmp_path)

    return store_image_complaint(result)

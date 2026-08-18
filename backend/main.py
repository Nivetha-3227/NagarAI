from fastapi import FastAPI, UploadFile, Form, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import traceback

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
    "https://nivetha-3227.github.io",
    "https://sheril07.github.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 2. BULLETPROOF CORS EXCEPTION HANDLER (The Fix)
# ============================================================
# When FastAPI encounters a 500 error or pipeline crash, it drops middleware 
# headers, causing a fake CORS error. This block forces CORS headers onto failures.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_trace = traceback.format_exc()
    print(f"CRASH LOG:\n{error_trace}") # Appears in your Render Terminal Logs
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Backend Pipeline Crash",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": error_trace
        },
        headers={
            "Access-Control-Allow-Origin": "https://nivetha-3227.github.io",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# ============================================================
# 3. DIAGNOSTIC CONNECTION TEST ROUTE
# ============================================================
# Hit this from your browser console to check if CORS is structurally alive
@app.get("/api/test-connection")
async def test_connection():
    return {"status": "success", "message": "CORS handshake is perfectly functional!"}

# ============================================================
# 4. COMPLAINT INTAKE PATHWAYS
# ============================================================

@app.post("/complaints/voice")
async def submit_voice(
    audio: UploadFile, 
    gps_lat: float = Form(None), 
    gps_lng: float = Form(None)
):
    pipeline = VoiceComplaintPipeline()
    result = pipeline.process(audio.file.name, gps_lat=gps_lat, gps_lng=gps_lng)
    return store_complaint_in_supabase(result, storage_path=audio.filename)


@app.post("/api/text-intake")
async def submit_text(payload: dict):
    text = payload.get("text", "")
    gps_lat = payload.get("gps_lat")
    gps_lng = payload.get("gps_lng")
    
    # This pipeline execution is likely missing a library or environment key, forcing the 500 error
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
    pipeline = ImageComplaintPipeline()
    result = pipeline.process(image.file.name, caption, gps_lat=gps_lat, gps_lng=gps_lng)
    return store_image_complaint(result)

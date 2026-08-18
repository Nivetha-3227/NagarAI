from fastapi import FastAPI, UploadFile, Form
from backend.pipelines.voice_pipeline import VoiceComplaintPipeline, store_complaint_in_supabase
from backend.pipelines.text_pipeline import TextComplaintPipeline, store_text_complaint
from backend.pipelines.image_pipeline import ImageComplaintPipeline, store_image_complaint

app = FastAPI(title="nagarAI Civic Complaint API")

@app.post("/complaint/voice")
async def submit_voice(audio: UploadFile, gps_lat: float = Form(None), gps_lng: float = Form(None)):
    pipeline = VoiceComplaintPipeline()
    result = pipeline.process(audio.file.name, gps_lat=gps_lat, gps_lng=gps_lng)
    return store_complaint_in_supabase(result, storage_path=audio.filename)

@app.post("/complaint/text")
async def submit_text(text: str = Form(...), gps_lat: float = Form(None), gps_lng: float = Form(None)):
    pipeline = TextComplaintPipeline()
    result = pipeline.process(text, gps_lat=gps_lat, gps_lng=gps_lng)
    return store_text_complaint(result)

@app.post("/complaint/image")
async def submit_image(image: UploadFile, caption: str = Form(...), gps_lat: float = Form(None), gps_lng: float = Form(None)):
    pipeline = ImageComplaintPipeline()
    result = pipeline.process(image.file.name, caption, gps_lat=gps_lat, gps_lng=gps_lng)
    return store_image_complaint(result)

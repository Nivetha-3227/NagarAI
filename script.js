const API_BASE_URL = "https://nagarai-x9xe.onrender.com";

let mediaRecorder;
let audioChunks = [];

// ---------- Helper: Capture Live GPS Coordinates ----------
function getLiveLocation() {
    const gpsText = document.getElementById("gpsText");

    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            if (gpsText) {
                gpsText.innerText = "❌ Not supported by browser";
            }
            reject("Geolocation is not supported by your browser.");
            return;
        }

        if (gpsText) {
            gpsText.innerText = "⌛ Locating...";
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const long = position.coords.longitude;

                if (gpsText) {
                    gpsText.innerText = `✅ Active (${lat.toFixed(4)}, ${long.toFixed(4)})`;
                }

                resolve({ lat, long });
            },
            (error) => {
                if (gpsText) {
                    gpsText.innerText = "❌ Permission Denied / Error";
                }
                reject("Location permission denied. Please allow location access.");
            }
        );
    });
}

// Check GPS status immediately when page loads
window.addEventListener("DOMContentLoaded", () => {
    getLiveLocation().catch((err) => {
        console.log("Initial GPS check:", err);
    });
});

// ============================================================
// 1A. VOICE COMPLAINT — MICROPHONE RECORDING
// ============================================================
const startBtn = document.getElementById("startRec");
const stopBtn = document.getElementById("stopRec");
const recStatus = document.getElementById("recStatus");
const statusDiv = document.getElementById("status");

if (startBtn && stopBtn) {
    startBtn.addEventListener("click", async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.start();
            startBtn.disabled = true;
            stopBtn.disabled = false;
            if (recStatus) {
                recStatus.innerText = "🔴 Recording... Speak clearly into your mic!";
            }
        } catch (err) {
            alert("Microphone access denied or not supported.");
        }
    });

    stopBtn.addEventListener("click", () => {
        if (!mediaRecorder) return;

        mediaRecorder.onstop = async () => {
            startBtn.disabled = false;
            stopBtn.disabled = true;

            mediaRecorder.stream.getTracks().forEach((track) => track.stop());

            const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
            const audioFile = new File([audioBlob], "recorded_complaint.webm", { type: "audio/webm" });

            try {
                if (statusDiv) statusDiv.innerText = "Submitting recorded voice complaint...";
                const coords = await getLiveLocation();
                const formData = new FormData();

                formData.append("audio", audioFile);
                formData.append("gps_lat", coords.lat);
                formData.append("gps_lng", coords.long);

                const response = await fetch(`${API_BASE_URL}/complaints/voice`, {
                    method: "POST",
                    body: formData
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.detail || `Server error: ${response.status}`);
                }

                if (statusDiv) {
                    statusDiv.innerText = "✅ Recorded Voice Submitted!\n\n" + JSON.stringify(result, null, 2);
                }
                if (recStatus) {
                    recStatus.innerText = "Click Start to record another complaint...";
                }
            } catch (err) {
                if (statusDiv) statusDiv.innerText = "❌ Error submitting recording: " + err.message;
                if (recStatus) recStatus.innerText = "Recording failed. Try again.";
            }
        };

        mediaRecorder.stop();
        if (recStatus) recStatus.innerText = "⏳ Processing audio & getting location...";
    });
}

// ============================================================
// 1B. VOICE COMPLAINT — FILE UPLOAD
// ============================================================
const voiceForm = document.getElementById("voiceForm");
if (voiceForm) {
    voiceForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById("audioFile");

        if (!fileInput || !fileInput.files[0]) {
            alert("Please select an audio file first.");
            return;
        }

        try {
            if (statusDiv) statusDiv.innerText = "Capturing location & uploading audio file...";
            const coords = await getLiveLocation();
            const formData = new FormData();

            formData.append("audio", fileInput.files[0]);
            formData.append("gps_lat", coords.lat);
            formData.append("gps_lng", coords.long);

            const response = await fetch(`${API_BASE_URL}/complaints/voice`, {
                method: "POST",
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || `Server error: ${response.status}`);
            }

            if (statusDiv) {
                statusDiv.innerText = "✅ Voice File Submitted!\n\n" + JSON.stringify(result, null, 2);
            }
            fileInput.value = "";
        } catch (err) {
            if (statusDiv) statusDiv.innerText = "❌ Error submitting voice file: " + err.message;
        }
    });
}

// ============================================================
// 2. TEXT COMPLAINT
// ============================================================
const textForm = document.getElementById("textForm");
if (textForm) {
    textForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const textInput = document.getElementById("textInput");

        if (!textInput || !textInput.value.trim()) {
            alert("Please enter a complaint description.");
            return;
        }

        try {
            if (statusDiv) statusDiv.innerText = "Capturing location & submitting text complaint...";
            const coords = await getLiveLocation();

            const payload = {
                text: textInput.value,
                gps_lat: coords.lat,
                gps_lng: coords.long
            };

            const response = await fetch(`${API_BASE_URL}/api/text-intake`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || `Server error: ${response.status}`);
            }

            if (statusDiv) {
                statusDiv.innerText = "✅ Text Complaint Submitted!\n\n" + JSON.stringify(result, null, 2);
            }
            textInput.value = "";
        } catch (err) {
            if (statusDiv) statusDiv.innerText = "❌ Error submitting text complaint: " + err.message;
        }
    });
}

const API_BASE_URL = "https://nagarai-webpage.onrender.com";

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
                    gpsText.innerText =
                        `✅ Active (${lat.toFixed(4)}, ${long.toFixed(4)})`;
                }

                resolve({
                    lat,
                    long
                });
            },

            (error) => {

                if (gpsText) {
                    gpsText.innerText =
                        "❌ Permission Denied / Error";
                }

                reject(
                    "Location permission denied. Please allow location access."
                );
            }
        );
    });
}


// Check GPS status immediately when page loads

window.addEventListener("DOMContentLoaded", () => {

    getLiveLocation()
        .catch((err) => {
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


startBtn.addEventListener("click", async () => {

    try {

        const stream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });

        mediaRecorder =
            new MediaRecorder(stream);

        audioChunks = [];


        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };


        mediaRecorder.start();

        startBtn.disabled = true;
        stopBtn.disabled = false;

        recStatus.innerText =
            "🔴 Recording... Speak clearly into your mic!";

    } catch (err) {

        alert(
            "Microphone access denied or not supported."
        );
    }
});


stopBtn.addEventListener("click", () => {

    // Attach onstop BEFORE calling stop() to avoid a race condition
    // where the 'stop' event could fire before the handler exists.
    mediaRecorder.onstop = async () => {

        startBtn.disabled = false;
        stopBtn.disabled = true;

        // Release the microphone so the browser's "mic in use"
        // indicator turns off once we're done recording.
        mediaRecorder.stream
            .getTracks()
            .forEach((track) => track.stop());


        const audioBlob =
            new Blob(audioChunks, {
                type: "audio/webm"
            });


        const audioFile =
            new File(
                [audioBlob],
                "recorded_complaint.webm",
                {
                    type: "audio/webm"
                }
            );


        try {

            statusDiv.innerText =
                "Submitting recorded voice complaint...";


            const coords =
                await getLiveLocation();


            const formData =
                new FormData();


            // Backend expects "audio"
            formData.append(
                "audio",
                audioFile
            );


            // Backend expects "gps_lat"
            formData.append(
                "gps_lat",
                coords.lat
            );


            // Backend expects "gps_lng"
            formData.append(
                "gps_lng",
                coords.long
            );


            const response =
                await fetch(
                    `${API_BASE_URL}/complaints/voice`,
                    {
                        method: "POST",
                        body: formData
                    }
                );


            const result =
                await response.json();


            if (!response.ok) {
                throw new Error(
                    result.detail ||
                    `Server error: ${response.status}`
                );
            }


            statusDiv.innerText =
                "✅ Recorded Voice Submitted!\n\n" +
                JSON.stringify(
                    result,
                    null,
                    2
                );


            recStatus.innerText =
                "Click Start to record another complaint...";


        } catch (err) {

            statusDiv.innerText =
                "❌ Error submitting recording: " +
                err.message;

            recStatus.innerText =
                "Recording failed. Try again.";
        }
    };

    mediaRecorder.stop();

    recStatus.innerText =
        "⏳ Processing audio & getting location...";
});


// ============================================================
// 1B. VOICE COMPLAINT — FILE UPLOAD
// ============================================================

document
    .getElementById("voiceForm")
    .addEventListener(
        "submit",
        async (e) => {

            e.preventDefault();


            const fileInput =
                document.getElementById("audioFile");


            if (!fileInput.files[0]) {

                alert(
                    "Please select an audio file first."
                );

                return;
            }


            try {

                statusDiv.innerText =
                    "Capturing location & uploading audio file...";


                const coords =
                    await getLiveLocation();


                const formData =
                    new FormData();


                // Backend expects "audio"
                formData.append(
                    "audio",
                    fileInput.files[0]
                );


                // Backend expects "gps_lat"
                formData.append(
                    "gps_lat",
                    coords.lat
                );


                // Backend expects "gps_lng"
                formData.append(
                    "gps_lng",
                    coords.long
                );


                const response =
                    await fetch(
                        `${API_BASE_URL}/complaints/voice`,
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                const result =
                    await response.json();


                if (!response.ok) {
                    throw new Error(
                        result.detail ||
                        `Server error: ${response.status}`
                    );
                }


                statusDiv.innerText =
                    "✅ Voice File Submitted!\n\n" +
                    JSON.stringify(
                        result,
                        null,
                        2
                    );


                fileInput.value = "";


            } catch (err) {

                statusDiv.innerText =
                    "❌ Error submitting voice file: " +
                    err.message;
            }
        }
    );


// ============================================================
// 2. TEXT COMPLAINT
// ============================================================

document
    .getElementById("textForm")
    .addEventListener(
        "submit",
        async (e) => {

            e.preventDefault();


            const textValue =
                document
                    .getElementById("textInput")
                    .value;


            try {

                statusDiv.innerText =
                    "Capturing location & submitting text complaint...";


                const coords =
                    await getLiveLocation();


                const formData =
                    new FormData();


                // Backend expects "text"
                formData.append(
                    "text",
                    textValue
                );


                // Backend expects "gps_lat"
                formData.append(
                    "gps_lat",
                    coords.lat
                );


                // Backend expects "gps_lng"
                formData.append(
                    "gps_lng",
                    coords.long
                );


                const response =
                    await fetch(
                        `${API_BASE_URL}/complaints/text`,
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                const result =
                    await response.json();


                if (!response.ok) {
                    throw new Error(
                        result.detail ||
                        `Server error: ${response.status}`
                    );
                }


                statusDiv.innerText =
                    "✅ Text Complaint Submitted!\n\n" +
                    JSON.stringify(
                        result,
                        null,
                        2
                    );


                document
                    .getElementById("textInput")
                    .value = "";


            } catch (err) {

                statusDiv.innerText =
                    "❌ Error submitting text complaint: " +
                    err.message;
            }
        }
    );


// ============================================================
// 3. IMAGE / PHOTO COMPLAINT
// ============================================================

document
    .getElementById("imageForm")
    .addEventListener(
        "submit",
        async (e) => {

            e.preventDefault();


            const imageFile =
                document
                    .getElementById("imageFile")
                    .files[0];


            const caption =
                document
                    .getElementById("imageCaption")
                    .value;


            if (!imageFile) {

                alert(
                    "Please select an image file first."
                );

                return;
            }


            try {

                statusDiv.innerText =
                    "Capturing location & uploading image...";


                const coords =
                    await getLiveLocation();


                const formData =
                    new FormData();


                // Backend expects "image"
                formData.append(
                    "image",
                    imageFile
                );


                // Backend currently does NOT define
                // a caption parameter, so don't send it.


                // Backend expects "gps_lat"
                formData.append(
                    "gps_lat",
                    coords.lat
                );


                // Backend expects "gps_lng"
                formData.append(
                    "gps_lng",
                    coords.long
                );


                const response =
                    await fetch(
                        `${API_BASE_URL}/complaints/photo`,
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                const result =
                    await response.json();


                if (!response.ok) {
                    throw new Error(
                        result.detail ||
                        `Server error: ${response.status}`
                    );
                }


                statusDiv.innerText =
                    "✅ Image Complaint Submitted!\n\n" +
                    JSON.stringify(
                        result,
                        null,
                        2
                    );


                document
                    .getElementById("imageFile")
                    .value = "";


                document
                    .getElementById("imageCaption")
                    .value = "";


            } catch (err) {

                statusDiv.innerText =
                    "❌ Error submitting image complaint: " +
                    err.message;
            }
        }
    );

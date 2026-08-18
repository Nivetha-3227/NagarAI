const API_BASE = "http://localhost:8000"; // adjust if deployed

async function submitVoice() {
  const fileInput = document.getElementById("voiceFile");
  if (!fileInput.files.length) return alert("Please select an audio file");

  const formData = new FormData();
  formData.append("audio", fileInput.files[0]);

  const res = await fetch(`${API_BASE}/complaint/voice`, {
    method: "POST",
    body: formData
  });
  const data = await res.json();
  document.getElementById("response").innerText = JSON.stringify(data, null, 2);
}

async function submitText() {
  const text = document.getElementById("textComplaint").value;
  if (!text) return alert("Please enter a complaint");

  const formData = new FormData();
  formData.append("text", text);

  const res = await fetch(`${API_BASE}/complaint/text`, {
    method: "POST",
    body: formData
  });
  const data = await res.json();
  document.getElementById("response").innerText = JSON.stringify(data, null, 2);
}

async function submitImage() {
  const fileInput = document.getElementById("imageFile");
  const caption = document.getElementById("imageCaption").value;
  if (!fileInput.files.length || !caption) return alert("Please select an image and enter a caption");

  const formData = new FormData();
  formData.append("image", fileInput.files[0]);
  formData.append("caption", caption);

  const res = await fetch(`${API_BASE}/complaint/image`, {
    method: "POST",
    body: formData
  });
  const data = await res.json();
  document.getElementById("response").innerText = JSON.stringify(data, null, 2);
}

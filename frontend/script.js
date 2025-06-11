console.log("Script loaded.");

const uploadForm = document.getElementById("uploadForm");
const voiceFileInput = document.getElementById("voiceFile");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const player = document.getElementById("player");

const uploadStatusMessage = document.getElementById("uploadStatusMessage");
const uploadErrorMessage = document.getElementById("uploadErrorMessage");
const recordStatusMessage = document.getElementById("recordStatusMessage");
const recordErrorMessage = document.getElementById("recordErrorMessage");

const uploadFilenameInput = document.getElementById("uploadFilenameInput");
const recordFilenameInput = document.getElementById("recordFilenameInput");

const fileSelect = document.getElementById("fileSelect");
const featuresOutput = document.getElementById("featuresOutput");

let mediaRecorder;
let audioChunks = [];

const BASE_URL = "http://localhost:5000";

function clearMessages() {
  uploadStatusMessage.textContent = "";
  uploadErrorMessage.textContent = "";
  recordStatusMessage.textContent = "";
  recordErrorMessage.textContent = "";
}

// Populate file dropdown
async function fetchFiles() {
  try {
    const res = await fetch(`${BASE_URL}/list_files`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const files = await res.json();

    fileSelect.innerHTML = "";
    if (files.length === 0) {
      const option = document.createElement("option");
      option.textContent = "No files found";
      option.disabled = true;
      fileSelect.appendChild(option);
      return;
    }

    files.forEach((filename) => {
      const option = document.createElement("option");
      option.value = filename;
      option.textContent = filename;
      fileSelect.appendChild(option);
    });
  } catch (err) {
    console.error("Error fetching files:", err);
    fileSelect.innerHTML = "<option disabled>Error loading files</option>";
  }
}

// Extract features for selected file
async function extractFeatures() {
  const selectedFile = fileSelect.value;
  if (!selectedFile || selectedFile === "No files found") {
    featuresOutput.textContent = "Please select a valid file first.";
    return;
  }

  featuresOutput.textContent = "Extracting features...";

  try {
    const res = await fetch(`${BASE_URL}/extract_features/${encodeURIComponent(selectedFile)}`);

    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      const data = await res.json();

      if (res.ok) {
        featuresOutput.textContent = JSON.stringify(data.features, null, 2);
      } else {
        featuresOutput.textContent = "Error: " + (data.error || JSON.stringify(data));
      }
    } else {
      const errorText = await res.text();
      featuresOutput.textContent = `Server Error (${res.status}): ${errorText.substring(0, 500)}...`;
    }
  } catch (err) {
    featuresOutput.textContent = "Failed to extract features: " + err.message;
  }
}

// Handle file upload
uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearMessages();

  const file = voiceFileInput.files[0];
  const filename = uploadFilenameInput.value.trim();

  if (!file) {
    uploadErrorMessage.textContent = "Please select a file to upload.";
    return;
  }

  if (!filename) {
    uploadErrorMessage.textContent = "Please enter a filename.";
    return;
  }

  const formData = new FormData();
  formData.append("voice", file, filename + ".wav");
  formData.append("custom_filename", filename + ".wav");

  try {
    const res = await fetch(`${BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    });

    const result = await res.text();
    if (res.ok) {
      uploadStatusMessage.textContent = "Voice uploaded successfully!";
      await fetchFiles(); // refresh file list
    } else {
      uploadErrorMessage.textContent = "Upload failed: " + result;
    }
  } catch (err) {
    uploadErrorMessage.textContent = "Upload error: " + err.message;
  }
});

// Start recording audio
startBtn.onclick = async () => {
  clearMessages();

  if (!recordFilenameInput.value.trim()) {
    recordErrorMessage.textContent = "Please enter a filename before recording.";
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

    mediaRecorder.onstop = async () => {
      const filename = recordFilenameInput.value.trim();
      if (!filename) {
        recordErrorMessage.textContent = "Filename lost. Please enter it again.";
        return;
      }

      // Create a Blob from the recorded audio chunks
      const blob = new Blob(audioChunks, { type: "audio/webm" });
      player.src = URL.createObjectURL(blob);

      const formData = new FormData();
      formData.append("voice", blob, filename + ".wav"); // Hacky: sending webm as wav for backend
      formData.append("custom_filename", filename + ".wav");

      try {
        const res = await fetch(`${BASE_URL}/upload`, {
          method: "POST",
          body: formData,
        });

        const result = await res.text();
        if (res.ok) {
          recordStatusMessage.textContent = "Recording uploaded successfully!";
          await fetchFiles(); // refresh file list
        } else {
          recordErrorMessage.textContent = "Upload failed: " + result;
        }
      } catch (err) {
        recordErrorMessage.textContent = "Upload error: " + err.message;
      }
    };

    mediaRecorder.start();
    startBtn.disabled = true;
    stopBtn.disabled = false;
  } catch (err) {
    recordErrorMessage.textContent = "Microphone access denied or not available.";
  }
};

// Stop recording audio
stopBtn.onclick = () => {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    startBtn.disabled = false;
    stopBtn.disabled = true;
  }
};

// Initialize
window.onload = fetchFiles;
document.getElementById("extractBtn").onclick = extractFeatures;

// ✅ NEW: Risk Profiling Logic
const riskForm = document.getElementById("riskForm");
const riskResult = document.getElementById("riskResult");

riskForm?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData(riskForm);
  const riskData = {};

  for (let [key, value] of formData.entries()) {
    if (key.includes("_intensity")) continue;
    const intensity = parseFloat(formData.get(`${key}_intensity`) || 0.5);
    riskData[key] = { emotion: value, intensity };
  }

  try {
    const res = await fetch(`${BASE_URL}/calculate_risk`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(riskData),
    });

    const data = await res.json();
    if (res.ok) {
      riskResult.textContent = `✅ Risk Score: ${data.risk_score} (${data.risk_category})`;
    } else {
      riskResult.textContent = `❌ Error: ${data.error || "Unknown error"}`;
    }
  } catch (err) {
    riskResult.textContent = `❌ Failed to submit: ${err.message}`;
  }
});

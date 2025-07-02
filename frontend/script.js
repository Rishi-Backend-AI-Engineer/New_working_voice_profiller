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

const BASE_URL = "http://localhost:5001";

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

// 🎯 Analyze Session
const analyzeBtn = document.getElementById("analyzeBtn");
const reportBtn = document.getElementById("reportBtn");
const analyzeStatus = document.getElementById("analyzeStatus");
const reportStatus = document.getElementById("reportStatus");

analyzeBtn.onclick = async () => {
  const filename = fileSelect.value;
  if (!filename) {
    analyzeStatus.textContent = "Please select a file to analyze.";
    return;
  }
  analyzeStatus.textContent = "Analyzing...";
  try {
    const res = await fetch(`${BASE_URL}/analyze/${filename}`);
    const data = await res.json();
    if (res.ok) {
      analyzeStatus.textContent = "✅ Session analyzed successfully!";
      console.log("📊 Full session object:", data.result);
      featuresOutput.textContent = JSON.stringify(data.result, null, 2);
    } else {
      analyzeStatus.textContent = "❌ " + (data.error || "Analysis failed.");
    }
  } catch (err) {
    analyzeStatus.textContent = "❌ Failed: " + err.message;
  }
};

// 📄 Generate Report
reportBtn.onclick = async () => {
  const filename = fileSelect.value;
  if (!filename) {
    reportStatus.textContent = "Please select a file.";
    return;
  }
  reportStatus.textContent = "Generating PDF...";
  try {
    const res = await fetch(`${BASE_URL}/generate_report/${filename}`);
    if (!res.ok) throw new Error("Server error");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filename}_report.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
    reportStatus.textContent = "✅ PDF downloaded!";
  } catch (err) {
    reportStatus.textContent = "❌ " + err.message;
  }
};

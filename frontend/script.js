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

let mediaRecorder, audioChunks;

function clearMessages() {
  uploadStatusMessage.textContent = "";
  uploadErrorMessage.textContent = "";
  recordStatusMessage.textContent = "";
  recordErrorMessage.textContent = "";
}

// Populate file dropdown
async function fetchFiles() {
  try {
    const res = await fetch("http://localhost:5000/list_files");
    const files = await res.json();

    fileSelect.innerHTML = "";
    files.forEach((filename) => {
      const option = document.createElement("option");
      option.value = filename;
      option.textContent = filename;
      fileSelect.appendChild(option);
    });
  } catch (err) {
    console.error("Error fetching files:", err);
  }
}

// Extract features
// async function extractFeatures() {
//   const selectedFile = fileSelect.value;
//   if (!selectedFile) return;

//   try {
//     const res = await fetch(`http://localhost:5000/extract_features/${selectedFile}`);
//     const data = await res.json();

//     if (res.ok) {
//       featuresOutput.textContent = JSON.stringify(data.features, null, 2);
//     } else {
//       featuresOutput.textContent = "Error: " + JSON.stringify(data);
//     }
//   } catch (err) {
//     featuresOutput.textContent = "Failed to extract features: " + err.message;
//   }
// }
// Extract features
async function extractFeatures() {
  const selectedFile = fileSelect.value;
  if (!selectedFile) {
    featuresOutput.textContent = "Please select a file first.";
    return;
  }

  featuresOutput.textContent = "Extracting features...";

  try {
    const res = await fetch(`http://localhost:5000/extract_features/${selectedFile}`);
    
    // Check if response is actually JSON
    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      const data = await res.json();
      
      if (res.ok) {
        featuresOutput.textContent = JSON.stringify(data.features, null, 2);
      } else {
        featuresOutput.textContent = "Error: " + (data.error || JSON.stringify(data));
      }
    } else {
      // Server returned HTML error page or plain text
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
    const res = await fetch("http://localhost:5000/upload", {
      method: "POST",
      body: formData,
    });

    const result = await res.text();
    if (res.ok) {
      uploadStatusMessage.textContent = "Voice uploaded successfully!";
      fetchFiles(); // refresh file list
    } else {
      uploadErrorMessage.textContent = "Upload failed: " + result;
    }
  } catch (err) {
    uploadErrorMessage.textContent = "Upload error: " + err.message;
  }
});

// Start recording
startBtn.onclick = async () => {
  clearMessages();

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
    mediaRecorder.onstop = async () => {
      const filename = recordFilenameInput.value.trim();

      if (!filename) {
        recordErrorMessage.textContent = "Please enter a filename before recording.";
        return;
      }

      const blob = new Blob(audioChunks, { type: "audio/wav" });
      player.src = URL.createObjectURL(blob);

      const formData = new FormData();
      formData.append("voice", blob, filename + ".wav");
      formData.append("custom_filename", filename + ".wav");

      try {
        const res = await fetch("http://localhost:5000/upload", {
          method: "POST",
          body: formData,
        });

        const result = await res.text();
        if (res.ok) {
          recordStatusMessage.textContent = "Recording uploaded successfully!";
          fetchFiles(); // refresh file list
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

// Stop recording
stopBtn.onclick = () => {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    startBtn.disabled = false;
    stopBtn.disabled = true;
  }
};

// On load
fetchFiles();
window.onload = fetchFiles;
document.getElementById("extractBtn").onclick = extractFeatures;
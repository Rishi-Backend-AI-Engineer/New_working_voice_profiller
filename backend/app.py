import os
import io
import librosa
import numpy as np
import soundfile as sf
import tempfile
from flask import Flask, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
from pymongo import MongoClient
from pydub import AudioSegment

# Flask setup
app = Flask(__name__)
CORS(app)

# Config
app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploads")
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

# MongoDB setup
client = MongoClient("mongodb://localhost:27018/")
db = client["ZTproj30"]

# --- Feature Extraction Utils ---
def compute_rhythm_features(audio, beat_frames, sample_rate):
    beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)
    intervals = np.diff(beat_times)
    return {
        "avg_beat_interval": np.mean(intervals) if len(intervals) > 0 else 0,
        "std_beat_interval": np.std(intervals) if len(intervals) > 0 else 0
    }

def extract_voice_quality(audio, sample_rate):
    zcr = librosa.feature.zero_crossing_rate(audio)[0]
    return {
        "zero_crossing_rate": np.mean(zcr)
    }

def extract_features(audio_data, feature_types=None):
    audio = audio_data["audio"]
    sample_rate = audio_data["sample_rate"]

    if feature_types is None:
        feature_types = ["mfcc", "spectral", "prosodic", "voice_quality"]

    features = {}

    if "mfcc" in feature_types:
        mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=13)
        delta_mfccs = librosa.feature.delta(mfccs)
        delta2_mfccs = librosa.feature.delta(mfccs, order=2)
        features["mfcc"] = {
            "mfcc": mfccs.tolist(),
            "delta_mfcc": delta_mfccs.tolist(),
            "delta2_mfcc": delta2_mfccs.tolist()
        }

    if "spectral" in feature_types:
        features["spectral"] = {
            "centroid": librosa.feature.spectral_centroid(y=audio, sr=sample_rate).tolist(),
            "bandwidth": librosa.feature.spectral_bandwidth(y=audio, sr=sample_rate).tolist(),
            "rolloff": librosa.feature.spectral_rolloff(y=audio, sr=sample_rate).tolist(),
            "contrast": librosa.feature.spectral_contrast(y=audio, sr=sample_rate).tolist()
        }

    if "prosodic" in feature_types:
        f0, voiced_flag, voiced_probs = librosa.pyin(audio, fmin=75, fmax=400)
        tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sample_rate)
        features["prosodic"] = {
            "f0": f0.tolist() if f0 is not None else [],
            "voiced_flag": voiced_flag.tolist() if voiced_flag is not None else [],
            "voiced_probs": voiced_probs.tolist() if voiced_probs is not None else [],
            "tempo": tempo,
            "rhythm": compute_rhythm_features(audio, beat_frames, sample_rate)
        }

    if "voice_quality" in feature_types:
        features["voice_quality"] = extract_voice_quality(audio, sample_rate)

    return features

# Upload route
@app.route("/upload", methods=["POST"])
def upload_voice():
    if "voice" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["voice"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    custom_filename = request.form.get("custom_filename", file.filename)
    custom_filename = secure_filename(custom_filename)

    # Save uploaded file temporarily
    temp_path = os.path.join(app.config["UPLOAD_FOLDER"], custom_filename)
    file.save(temp_path)

    # Detect format (e.g., webm or wav) from extension
    ext = os.path.splitext(custom_filename)[1].lower()
    try:
        if ext != ".wav":
            # Convert to wav using pydub + ffmpeg
            audio = AudioSegment.from_file(temp_path)
            temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            audio.export(temp_wav.name, format="wav")
            with open(temp_wav.name, "rb") as f:
                voice_binary = f.read()
            os.remove(temp_wav.name)
        else:
            with open(temp_path, "rb") as f:
                voice_binary = f.read()
    finally:
        os.remove(temp_path)

    # Save to MongoDB
    db.voices.insert_one({
        "filename": custom_filename if custom_filename.endswith(".wav") else custom_filename + ".wav",
        "file": voice_binary
    })

    return jsonify({"message": "Voice uploaded successfully"}), 200

# List all uploaded filenames
@app.route("/list_files", methods=["GET"])
def list_files():
    filenames = db.voices.distinct("filename")
    return jsonify(filenames)

# Extract features for a given filename

@app.route('/extract_features', methods=['POST'])
def extract_features():
    try:
        data = request.json
        filename = data['filename']
        
        # Get the file from MongoDB
        record = collection.find_one({"filename": filename})
        if not record:
            return jsonify({"error": "File not found"}), 404
        
        audio_data = record['audio']
        
        # Convert raw bytes to WAV using pydub + ffmpeg
        audio_segment = AudioSegment.from_file(BytesIO(audio_data), format="wav")
        buf = BytesIO()
        audio_segment.export(buf, format="wav")
        buf.seek(0)

        # Now load with librosa
        y, sr = librosa.load(buf, sr=None)

        # Extract MFCCs (you can expand this)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1).tolist()

        return jsonify({
            "filename": filename,
            "mfcc_mean": mfcc_mean
        })

    except Exception as e:
        return jsonify({"error": "Feature extraction failed", "details": str(e)}), 500
# Serve frontend
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('../frontend', path)

# Run app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

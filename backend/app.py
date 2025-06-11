import os
os.environ['NUMBA_CACHE_DIR'] = '/tmp/numba-cache'
import io
import librosa
import numpy as np
import soundfile as sf
import tempfile
import traceback
from flask import Flask, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
from pymongo import MongoClient, errors
from pydub import AudioSegment
from dotenv import load_dotenv
from datetime import datetime
from pymongo import MongoClient, errors

# === Flask App Config ===
app = Flask(__name__)
CORS(app)

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR

# === MongoDB Setup ===
load_dotenv()
mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017")
db_name = os.getenv("DB_NAME", "voices")

try:
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client[db_name]
    client.admin.command('ping')
    print("✅ MongoDB connection successful")
except errors.ServerSelectionTimeoutError as err:
    print("❌ MongoDB connection failed:", err)
    db = None

# === Import Risk Profiler Logic ===
from services.risk_profiler import calculate_risk_profile

# === Utility Functions ===
def safe_float(x):
    try:
        x = float(x)
        return 0.0 if np.isnan(x) or np.isinf(x) else x
    except:
        return 0.0

def safe_mean(x): return safe_float(np.mean(x))
def safe_std(x): return safe_float(np.std(x))

def extract_audio_features(audio_data):
    try:
        y, sr = audio_data["audio"], audio_data["sample_rate"]
        features = {}

        # --- Pitch (NO pyin) ---
        pitches, mags = librosa.piptrack(y=y, sr=sr)
        pitch_vals = pitches[pitches > 0]
        features["pitch"] = {
            "average_pitch_hz": safe_mean(pitch_vals),
            "pitch_range_hz": safe_float(np.max(pitch_vals) - np.min(pitch_vals)) if len(pitch_vals) > 0 else 0.0,
            "pitch_stability": 0.0,  # Optional: hard to compute without pyin
            "voiced_percentage": 0.0  # Skipped for now
        }
        # --- Loudness ---
        rms = librosa.feature.rms(y=y)[0]
        spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        features["loudness"] = {
            "average_loudness_db": safe_float(20 * np.log10(safe_mean(rms) + 1e-10)),
            "loudness_variation": safe_std(rms),
            "dynamic_range_db": safe_float(20 * np.log10((np.max(rms)+1e-10) / (np.min(rms)+1e-10))),
            "spectral_brightness": safe_mean(spec_cent)
        }
        # --- Rhythm (no beat_track) ---
        features["rhythm"] = {
            "estimated_tempo_bpm": 0.0,  # Skipped
            "speech_rate_syllables_per_sec": 0.0,
            "rhythm_regularity": 0.0
        }

        # --- Voice Quality ---
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        shimmer = safe_std(rms) / safe_mean(rms)

        features["voice_quality"] = {
            "jitter_percentage": 0.0,  # Skipped
            "shimmer_percentage": safe_float(shimmer * 100),
            "harmonics_to_noise_ratio": 0.0,
            "voice_breaks_percentage": 0.0,
            "roughness_index": safe_mean(zcr),
            "breathiness_index": safe_mean(rolloff) / (sr / 2)
        }
        # --- Spectral ---
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)

        features["spectral"] = {
            "formant_concentration": safe_mean(mfccs[1:4]),
            "spectral_balance": safe_mean(contrast),
            "frequency_range_hz": safe_mean(bandwidth),
            "voice_timbre_brightness": safe_mean(spec_cent),
            "nasality_index": safe_mean(mfccs[2])
        }

        # --- Summary ---
        duration = len(y) / sr
        vq = features["voice_quality"]
        features["summary"] = {
            "audio_duration_seconds": safe_float(duration),
            "sample_rate_hz": int(sr),
            "overall_voice_health_score": safe_float(
                (100 - vq["shimmer_percentage"] * 5)
            ),
            "speech_clarity_score": safe_float(
                100 - vq["roughness_index"] * 100
            )
        }

        return features

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}


# === Routes ===
@app.route("/upload", methods=["POST"])
def upload_voice():
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500

    file = request.files.get("voice")
    if not file or file.filename == "":
        return jsonify({"error": "No file uploaded"}), 400

    filename = secure_filename(request.form.get("custom_filename", file.filename))
    if not filename.lower().endswith(".wav"):
        filename += ".wav"

    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)
    try:
        ext = os.path.splitext(filename)[1].lower()
        if ext != ".wav":
            try:
                audio = AudioSegment.from_file(path)
                wav_temp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                audio.export(wav_temp.name, format="wav")
                with open(wav_temp.name, "rb") as f:
                    voice_bytes = f.read()
                os.remove(wav_temp.name)
            except Exception as e:
                return jsonify({"error": f"Audio conversion failed: {str(e)}"}), 500
        else:
            with open(path, "rb") as f:
                voice_bytes = f.read()

            try:
                db.voices.insert_one({
                    "filename": filename,
                    "file": voice_bytes
                })
            except Exception as e:
                print("❌ Mongo insert failed:", str(e))
                return jsonify({"error": f"Mongo insert failed: {str(e)}"}), 500


        return jsonify({"message": "Uploaded successfully"})

    finally:
        if os.path.exists(path):
            os.remove(path)
@app.route("/list_files", methods=["GET"])
def list_files():
    if db is None:
        return jsonify([]), 200
    return jsonify(db.voices.distinct("filename"))

@app.route("/extract_features/<filename>", methods=["GET"])
def extract_features_route(filename):
    if db is None:
        return jsonify({"error": "DB unavailable"}), 500

    record = db.voices.find_one({"filename": filename})
    if not record:
        return jsonify({"error": "File not found"}), 404

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp.write(record["file"])
    temp.flush()

    try:
        try:
            y, sr = librosa.load(temp.name, sr=None)
        except Exception:
            audio = AudioSegment.from_file(temp.name)
            temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            audio.export(temp_wav.name, format="wav")
            y, sr = librosa.load(temp_wav.name, sr=None)
            os.remove(temp_wav.name)

        audio_data = {"audio": y, "sample_rate": sr}
        features = extract_audio_features(audio_data)
        return jsonify({"filename": filename, "features": features})

    except Exception as e:
        return jsonify({"error": f"Feature extraction failed: {str(e)}"}), 500
    finally:
        os.remove(temp.name)
        if 'temp_wav' in locals():
            os.remove(temp_wav.name)

from datetime import datetime
import traceback

@app.route("/calculate_risk", methods=["POST"])
def calculate_risk():
    if db is None:
        return jsonify({"error": "DB unavailable"}), 500
    try:
        user_input = request.json  # JSON like { "sensex_down_20": { "emotion": "...", "intensity": 0.7 }, ... }
        print("🧪 Received risk input:", user_input)

        result = calculate_risk_profile(user_input)
        print("✅ Calculated risk profile:", result)

        # Store in MongoDB
        db.risk_profiles.insert_one({
            "timestamp": datetime.utcnow(),
            "inputs": user_input,
            "result": result
        })
        print("📝 Inserted risk profile into MongoDB successfully.")

        return jsonify(result)

    except Exception as e:
        print("❌ Exception in /calculate_risk:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/")
def serve_index():
    return send_from_directory(os.path.join(app.root_path, "../frontend"), "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(os.path.join(app.root_path, "../frontend"), path)
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

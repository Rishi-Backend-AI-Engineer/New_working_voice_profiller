import os
import io
import traceback
import tempfile
from datetime import datetime
import psutil
import librosa
import numpy as np
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pydub import AudioSegment
from pymongo import MongoClient, errors
from dotenv import load_dotenv

from services.risk_profiler import calculate_risk_profile
from services.transcription import transcribe_audio
from services.nlp_analysis import analyze_text_features
from services.report_generator import generate_pdf
from services.recommender import generate_recommendations
from services.audio_features import extract_audio_features
from services.emotion_detector import detect_emotion
from services.emotion_detector import preload_model
preload_model()  # ✅ Model loads at app boot time, not per request

# === App Setup ===
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

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
    print("✅ MongoDB connection successful")
except errors.ServerSelectionTimeoutError as err:
    print("❌ MongoDB connection failed:", err)
    db = None

@app.route("/upload", methods=["POST"])
def upload_voice():
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500

    file = request.files.get("voice")
    if not file or file.filename == "":
        return jsonify({"error": "No file uploaded"}), 400

    original_filename = secure_filename(file.filename)
    custom_name = request.form.get("custom_filename", os.path.splitext(original_filename)[0])
    filename = f"{os.path.splitext(custom_name)[0]}.wav"  # avoid double .wav

    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    try:
        audio = AudioSegment.from_file(file.stream)
        audio.export(path, format="wav")

        with open(path, "rb") as f:
            voice_bytes = f.read()

        db.voices.replace_one(
            {"filename": filename},
            {"filename": filename, "file": voice_bytes},
            upsert=True
        )
        return jsonify({"message": "Uploaded and converted successfully"})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# === List Uploaded Files ===
@app.route("/list_files", methods=["GET"])
def list_files():
    if db is None:
        response = jsonify([])
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 200
    response = jsonify(db.voices.distinct("filename"))
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

# === extract features from uploaded voice ===
@app.route("/extract_features/<filename>", methods=["GET"])
def extract_features_route(filename):
    if db is None:
        response = jsonify({"error": "DB unavailable"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 500

    record = db.voices.find_one({"filename": filename})
    if not record:
        response = jsonify({"error": "Voice file not found"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 404

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp.write(record["file"])
    temp.flush()

    try:
        y, sr = librosa.load(temp.name, sr=None, duration=5.0)  # Limit duration for memory
        audio_data = {"audio": y, "sample_rate": sr}
        features = extract_audio_features(audio_data)

        response = jsonify({"filename": filename, "features": features})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except Exception as e:
        traceback.print_exc()
        response = jsonify({"error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 500

    finally:
        os.remove(temp.name)

@app.route("/analyze/<filename>", methods=["GET"])
def analyze_session(filename):
    if db is None:
        return jsonify({"error": "DB unavailable"}), 500

    voice_record = db.voices.find_one({"filename": filename})
    if not voice_record:
        return jsonify({"error": "Voice file not found"}), 404

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio_segment = AudioSegment.from_file(io.BytesIO(voice_record["file"]), format="wav")
    audio_segment.export(temp.name, format="wav")

    try:
        # 🔊 Extract audio features
        y, sr = librosa.load(temp.name, sr=None, duration=5.0)
        audio_data = {"audio": y, "sample_rate": sr}
        audio_features = extract_audio_features(audio_data)

        # 🎭 Emotion detection on full audio
        voice_emotion = detect_emotion(temp.name)

        # 🧠 Transcription + NLP on full audio
        with open(temp.name, "rb") as f:
            audio_bytes = f.read()
        transcript_result = transcribe_audio(audio_bytes)
        nlp_result = analyze_text_features(transcript_result["transcript"])

        # 📉 Generate pseudo-emotion input for each scenario trigger
        # Dynamic trigger-to-risk mapping based on intents
        intents = nlp_result.get("intents", [])
        sentiment_score = nlp_result.get("sentiment", {}).get("compound", 0)

        pseudo_emotion_input = {}

        if "risk" in intents:
            pseudo_emotion_input["sensex_down_20"] = {
                "emotion": "stress",
                "intensity": abs(sentiment_score)
            }

        if "lockin" in intents or "retirement" in intents:
            pseudo_emotion_input["lockin_period"] = {
                "emotion": "hesitation",
                "intensity": 0.7 + abs(sentiment_score) * 0.3
            }

        if "inflation" in intents:
            pseudo_emotion_input["inflation_impact"] = {
                "emotion": "fearful",
                "intensity": 0.5 + abs(sentiment_score) * 0.5
            }

        if "goal" in intents:
            pseudo_emotion_input["goal_confidence"] = {
                "emotion": "confidence" if sentiment_score > 0 else "doubt",
                "intensity": abs(sentiment_score)
            }

        # Fallback to ensure non-empty dict
        if not pseudo_emotion_input:
            pseudo_emotion_input["general"] = {
                "emotion": voice_emotion.get("label", "neutral"),
                "intensity": voice_emotion.get("score", 0.5)
            }


        # 📉 Risk profiling (correct structure)
        risk_result = calculate_risk_profile(pseudo_emotion_input, voice_emotion=voice_emotion)
        recommendations = generate_recommendations(risk_result, nlp_result)

        session_doc = {
            "filename": filename,
            "timestamp": datetime.utcnow(),
            "transcript": transcript_result["transcript"],
            "segments": transcript_result["segments"],
            "audio_features": audio_features,
            "voice_emotion": voice_emotion,
            "nlp_analysis": nlp_result,
            "risk_profile": risk_result,
            "recommendations": recommendations,
            "pdf_generated": False
        }

        db.sessions.replace_one({"filename": filename}, session_doc, upsert=True)
        return jsonify({"status": "ok", "result": session_doc})
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        os.remove(temp.name)


# === Generate PDF Report ===
@app.route("/generate_report/<filename>", methods=["GET"])
def generate_report(filename):
    if db is None:
        response = jsonify({"error": "DB unavailable"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 500

    record = db.sessions.find_one({"filename": filename})
    if not record:
        esponse = jsonify({"error": "Session not found"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 404

    pdf_buffer = generate_pdf(record, filename=filename)
    db.sessions.update_one({"filename": filename}, {"$set": {"pdf_generated": True}})
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{filename}_report.pdf"
    )

# === List All Sessions ===
@app.route("/sessions", methods=["GET"])
def list_sessions():
    if db is None:
        response = jsonify([])
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 200
    sessions = db.sessions.find({}, {"filename": 1, "timestamp": 1, "pdf_generated": 1})
    response = jsonify([s for s in sessions])
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

# === Serve Frontend ===
@app.route("/")
def serve_index():
    return send_from_directory(os.path.join(app.root_path, "../frontend"), "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(os.path.join(app.root_path, "../frontend"), path)

# Preload emotion model once at startup
from services.emotion_detector import preload_model
preload_model()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

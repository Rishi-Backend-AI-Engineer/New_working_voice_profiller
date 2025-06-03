import os
import io
import librosa
import numpy as np
import soundfile as sf
import tempfile
from io import BytesIO
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

# # --- Feature Extraction Utils ---
# def compute_rhythm_features(audio, beat_frames, sample_rate):
#     beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)
#     intervals = np.diff(beat_times)
#     return {
#         "avg_beat_interval": np.mean(intervals) if len(intervals) > 0 else 0,
#         "std_beat_interval": np.std(intervals) if len(intervals) > 0 else 0
#     }

# def extract_voice_quality(audio, sample_rate):
#     zcr = librosa.feature.zero_crossing_rate(audio)[0]
#     return {
#         "zero_crossing_rate": np.mean(zcr)
#     }
# def extract_audio_features(audio_data, feature_types=None):
# # def extract_features(audio_data, feature_types=None):
#     audio = audio_data["audio"]
#     sample_rate = audio_data["sample_rate"]

#     if feature_types is None:
#         feature_types = ["mfcc", "spectral", "prosodic", "voice_quality"]

#     features = {}

#     if "mfcc" in feature_types:
#         mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=13)
#         delta_mfccs = librosa.feature.delta(mfccs)
#         delta2_mfccs = librosa.feature.delta(mfccs, order=2)
#         features["mfcc"] = {
#             "mfcc": mfccs.tolist(),
#             "delta_mfcc": delta_mfccs.tolist(),
#             "delta2_mfcc": delta2_mfccs.tolist()
#         }

#     if "spectral" in feature_types:
#         features["spectral"] = {
#             "centroid": librosa.feature.spectral_centroid(y=audio, sr=sample_rate).tolist(),
#             "bandwidth": librosa.feature.spectral_bandwidth(y=audio, sr=sample_rate).tolist(),
#             "rolloff": librosa.feature.spectral_rolloff(y=audio, sr=sample_rate).tolist(),
#             "contrast": librosa.feature.spectral_contrast(y=audio, sr=sample_rate).tolist()
#         }

#     if "prosodic" in feature_types:
#         f0, voiced_flag, voiced_probs = librosa.pyin(audio, fmin=75, fmax=400)
#         tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sample_rate)
#         features["prosodic"] = {
#             "f0": f0.tolist() if f0 is not None else [],
#             "voiced_flag": voiced_flag.tolist() if voiced_flag is not None else [],
#             "voiced_probs": voiced_probs.tolist() if voiced_probs is not None else [],
#             "tempo": tempo,
#             "rhythm": compute_rhythm_features(audio, beat_frames, sample_rate)
#         }

#     if "voice_quality" in feature_types:
#         features["voice_quality"] = extract_voice_quality(audio, sample_rate)

#     return features
# def compute_rhythm_features(audio, beat_frames, sample_rate):
#     try:
#         beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)
#         intervals = np.diff(beat_times)
        
#         avg_interval = float(np.mean(intervals)) if len(intervals) > 0 else 0.0
#         std_interval = float(np.std(intervals)) if len(intervals) > 0 else 0.0
        
#         # Handle NaN values
#         if np.isnan(avg_interval) or np.isinf(avg_interval):
#             avg_interval = 0.0
#         if np.isnan(std_interval) or np.isinf(std_interval):
#             std_interval = 0.0
            
#         return {
#             "avg_beat_interval": avg_interval,
#             "std_beat_interval": std_interval
#         }
#     except Exception as e:
#         print(f"Rhythm features error: {e}")
#         return {
#             "avg_beat_interval": 0.0,
#             "std_beat_interval": 0.0
#         }

# def extract_voice_quality(audio, sample_rate):
#     try:
#         zcr = librosa.feature.zero_crossing_rate(audio)[0]
#         zcr_mean = float(np.mean(zcr))
        
#         # Handle NaN values
#         if np.isnan(zcr_mean) or np.isinf(zcr_mean):
#             zcr_mean = 0.0
            
#         return {
#             "zero_crossing_rate": zcr_mean
#         }
#     except Exception as e:
#         print(f"Voice quality error: {e}")
#         return {
#             "zero_crossing_rate": 0.0
#         }
    
# def extract_audio_features(audio_data, feature_types=None):
#     audio = audio_data["audio"]
#     sample_rate = audio_data["sample_rate"]

#     if feature_types is None:
#         feature_types = ["mfcc", "spectral", "prosodic", "voice_quality"]

#     features = {}

#     def clean_array(arr):
#         """Convert numpy array to list and replace NaN/inf with None"""
#         if arr is None:
#             return []
#         arr_list = arr.tolist() if hasattr(arr, 'tolist') else arr
#         if isinstance(arr_list, list):
#             return [None if (isinstance(x, float) and (np.isnan(x) or np.isinf(x))) else x for x in arr_list]
#         elif isinstance(arr_list, (int, float)):
#             return None if (isinstance(arr_list, float) and (np.isnan(arr_list) or np.isinf(arr_list))) else arr_list
#         return arr_list

#     def clean_2d_array(arr):
#         """Convert 2D numpy array to list and replace NaN/inf with None"""
#         if arr is None:
#             return []
#         arr_list = arr.tolist() if hasattr(arr, 'tolist') else arr
#         if isinstance(arr_list, list) and len(arr_list) > 0 and isinstance(arr_list[0], list):
#             return [[None if (isinstance(x, float) and (np.isnan(x) or np.isinf(x))) else x for x in row] for row in arr_list]
#         return clean_array(arr_list)

#     try:
#         if "mfcc" in feature_types:
#             mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=13)
#             delta_mfccs = librosa.feature.delta(mfccs)
#             delta2_mfccs = librosa.feature.delta(mfccs, order=2)
#             features["mfcc"] = {
#                 "mfcc": clean_2d_array(mfccs),
#                 "delta_mfcc": clean_2d_array(delta_mfccs),
#                 "delta2_mfcc": clean_2d_array(delta2_mfccs)
#             }
#     except Exception as e:
#         print(f"MFCC extraction failed: {e}")
#         features["mfcc"] = {"error": str(e)}

#     try:
#         if "spectral" in feature_types:
#             features["spectral"] = {
#                 "centroid": clean_array(librosa.feature.spectral_centroid(y=audio, sr=sample_rate)[0]),
#                 "bandwidth": clean_array(librosa.feature.spectral_bandwidth(y=audio, sr=sample_rate)[0]),
#                 "rolloff": clean_array(librosa.feature.spectral_rolloff(y=audio, sr=sample_rate)[0]),
#                 "contrast": clean_2d_array(librosa.feature.spectral_contrast(y=audio, sr=sample_rate))
#             }
#     except Exception as e:
#         print(f"Spectral extraction failed: {e}")
#         features["spectral"] = {"error": str(e)}

#     try:
#         if "prosodic" in feature_types:
#             f0, voiced_flag, voiced_probs = librosa.pyin(audio, fmin=75, fmax=400)
#             tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sample_rate)
            
#             features["prosodic"] = {
#                 "f0": clean_array(f0),
#                 "voiced_flag": clean_array(voiced_flag),
#                 "voiced_probs": clean_array(voiced_probs),
#                 "tempo": clean_array(tempo),
#                 "rhythm": compute_rhythm_features(audio, beat_frames, sample_rate)
#             }
#     except Exception as e:
#         print(f"Prosodic extraction failed: {e}")
#         features["prosodic"] = {"error": str(e)}

#     try:
#         if "voice_quality" in feature_types:
#             features["voice_quality"] = extract_voice_quality(audio, sample_rate)
#     except Exception as e:
#         print(f"Voice quality extraction failed: {e}")
#         features["voice_quality"] = {"error": str(e)}

#     return features

def extract_audio_features(audio_data, feature_types=None):
    audio = audio_data["audio"]
    sample_rate = audio_data["sample_rate"]

    features = {}

    def safe_float(value):
        """Convert to float and handle NaN/inf values"""
        try:
            if np.isnan(value) or np.isinf(value):
                return 0.0
            return float(value)
        except:
            return 0.0

    def safe_mean(arr):
        """Calculate safe mean of array"""
        try:
            return safe_float(np.mean(arr))
        except:
            return 0.0

    def safe_std(arr):
        """Calculate safe standard deviation of array"""
        try:
            return safe_float(np.std(arr))
        except:
            return 0.0

    try:
        # === PITCH ANALYSIS ===
        f0, voiced_flag, voiced_probs = librosa.pyin(audio, fmin=75, fmax=400)
        f0_clean = f0[~np.isnan(f0)] if f0 is not None else []
        
        pitch_features = {
            "average_pitch_hz": safe_mean(f0_clean),
            "pitch_range_hz": safe_float(np.max(f0_clean) - np.min(f0_clean)) if len(f0_clean) > 0 else 0.0,
            "pitch_stability": safe_float(1.0 - (np.std(f0_clean) / np.mean(f0_clean))) if len(f0_clean) > 0 and np.mean(f0_clean) > 0 else 0.0,
            "voiced_percentage": safe_float(np.mean(voiced_flag)) * 100 if voiced_flag is not None else 0.0
        }
        features["pitch"] = pitch_features

        # === LOUDNESS/ENERGY ANALYSIS ===
        rms_energy = librosa.feature.rms(y=audio)[0]
        spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sample_rate)[0]
        
        loudness_features = {
            "average_loudness_db": safe_float(20 * np.log10(safe_mean(rms_energy) + 1e-10)),
            "loudness_variation": safe_std(rms_energy),
            "dynamic_range_db": safe_float(20 * np.log10((np.max(rms_energy) + 1e-10) / (np.min(rms_energy) + 1e-10))),
            "spectral_brightness": safe_mean(spectral_centroid)
        }
        features["loudness"] = loudness_features

        # === SPEECH RATE AND RHYTHM ===
        tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sample_rate)
        onset_frames = librosa.onset.onset_detect(y=audio, sr=sample_rate)
        onset_times = librosa.frames_to_time(onset_frames, sr=sample_rate)
        
        rhythm_features = {
            "estimated_tempo_bpm": safe_float(tempo),
            "speech_rate_syllables_per_sec": safe_float(len(onset_frames) / (len(audio) / sample_rate)),
            "rhythm_regularity": safe_float(1.0 / (safe_std(np.diff(onset_times)) + 1e-10)) if len(onset_times) > 1 else 0.0
        }
        features["rhythm"] = rhythm_features

        # === VOICE QUALITY ===
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sample_rate)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sample_rate)[0]
        
        # Jitter and Shimmer approximations
        f0_periods = 1.0 / (f0_clean + 1e-10) if len(f0_clean) > 0 else [0]
        jitter = safe_std(f0_periods) / safe_mean(f0_periods) if len(f0_periods) > 1 else 0.0
        shimmer = safe_std(rms_energy) / safe_mean(rms_energy) if len(rms_energy) > 0 else 0.0
        
        voice_quality_features = {
            "jitter_percentage": safe_float(jitter * 100),
            "shimmer_percentage": safe_float(shimmer * 100),
            "harmonics_to_noise_ratio": safe_float(np.mean(voiced_probs)) * 20 if voiced_probs is not None else 0.0,
            "voice_breaks_percentage": safe_float((1 - np.mean(voiced_flag)) * 100) if voiced_flag is not None else 0.0,
            "roughness_index": safe_mean(zcr),
            "breathiness_index": safe_mean(spectral_rolloff) / (sample_rate / 2)
        }
        features["voice_quality"] = voice_quality_features

        # === SPECTRAL CHARACTERISTICS ===
        mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=13)
        spectral_contrast = librosa.feature.spectral_contrast(y=audio, sr=sample_rate)
        
        spectral_features = {
            "formant_concentration": safe_mean(mfccs[1:4]),  # Approximation using MFCC 1-3
            "spectral_balance": safe_mean(spectral_contrast),
            "frequency_range_hz": safe_mean(spectral_bandwidth),
            "voice_timbre_brightness": safe_mean(spectral_centroid),
            "nasality_index": safe_mean(mfccs[2])  # MFCC-2 often relates to nasality
        }
        features["spectral"] = spectral_features

        # === OVERALL SUMMARY ===
        duration_seconds = len(audio) / sample_rate
        
        summary = {
            "audio_duration_seconds": safe_float(duration_seconds),
            "sample_rate_hz": int(sample_rate),
            "overall_voice_health_score": safe_float(
                (100 - voice_quality_features["jitter_percentage"] * 10) *
                (100 - voice_quality_features["shimmer_percentage"] * 5) *
                (voice_quality_features["harmonics_to_noise_ratio"] / 20) / 10000
            ),
            "speech_clarity_score": safe_float(
                pitch_features["voiced_percentage"] * 
                (1 - voice_quality_features["voice_breaks_percentage"] / 100) * 
                min(1.0, voice_quality_features["harmonics_to_noise_ratio"] / 10)
            )
        }
        features["summary"] = summary

    except Exception as e:
        print(f"Feature extraction error: {e}")
        features["error"] = f"Feature extraction failed: {str(e)}"

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

# @app.route('/extract_features', methods=['POST'])
# def extract_features():
#     try:
#         data = request.json
#         filename = data['filename']
        
#         # Get the file from MongoDB
#         record = collection.find_one({"filename": filename})
#         if not record:
#             return jsonify({"error": "File not found"}), 404
        
#         audio_data = record['audio']
        
#         # Convert raw bytes to WAV using pydub + ffmpeg
#         audio_segment = AudioSegment.from_file(BytesIO(audio_data), format="wav")
#         buf = BytesIO()
#         audio_segment.export(buf, format="wav")
#         buf.seek(0)

#         # Now load with librosa
#         y, sr = librosa.load(buf, sr=None)

#         # Extract MFCCs (you can expand this)
#         mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
#         mfcc_mean = np.mean(mfcc, axis=1).tolist()

#         return jsonify({
#             "filename": filename,
#             "mfcc_mean": mfcc_mean
#         })

#     except Exception as e:
#         return jsonify({"error": "Feature extraction failed", "details": str(e)}), 500

@app.route('/extract_features/<filename>', methods=['GET'])
def extract_features_route(filename):
    temp_file_path = None
    try:
        print(f"Attempting to extract features for: {filename}")
        
        # Get the file from MongoDB
        record = db.voices.find_one({"filename": filename})
        if not record:
            print(f"File not found in database: {filename}")
            return jsonify({"error": "File not found"}), 404
        
        audio_binary = record['file']
        print(f"Retrieved audio file, size: {len(audio_binary)} bytes")
        
        # Create a temporary file to load with librosa
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_binary)
            temp_file.flush()
            temp_file_path = temp_file.name
            print(f"Created temp file: {temp_file_path}")
        
        # Verify the temp file exists and has content
        if not os.path.exists(temp_file_path):
            raise Exception("Temporary file was not created")
        
        file_size = os.path.getsize(temp_file_path)
        print(f"Temp file size: {file_size} bytes")
        
        if file_size == 0:
            raise Exception("Temporary file is empty")
        
        # Load with librosa
        print("Loading audio with librosa...")
        y, sr = librosa.load(temp_file_path, sr=None)
        print(f"Audio loaded successfully. Length: {len(y)}, Sample rate: {sr}")
        
        # Create audio_data dict for the extract_features function
        audio_data = {
            "audio": y,
            "sample_rate": sr
        }
        
        # Extract features using your existing function
        print("Extracting features...")
        features = extract_audio_features(audio_data)
        print("Features extracted successfully")
        
        return jsonify({
            "filename": filename,
            "features": features
        })

    except Exception as e:
        print(f"Error during feature extraction: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Feature extraction failed", "details": str(e)}), 500
    
    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"Cleaned up temp file: {temp_file_path}")
            except Exception as cleanup_error:
                print(f"Failed to clean up temp file: {cleanup_error}")
                
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

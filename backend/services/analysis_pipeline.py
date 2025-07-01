# services/analysis_pipeline.py

from services.nlp_analysis import analyze_text_features
from app import extract_audio_features, calculate_risk_profile, transcribe_audio
import librosa
import tempfile

def analyze_pipeline(audio_bytes, voice_emotion=None):
    # Step 1: Transcribe audio
    transcription_data = transcribe_audio(audio_bytes)
    transcript = transcription_data["transcript"]

    # Step 2: Load audio for features
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio.flush()
        y, sr = librosa.load(temp_audio.name, sr=None)

    audio_data = {"audio": y, "sample_rate": sr}
    features = extract_audio_features(audio_data)

    # Step 3: NLP
    nlp_analysis = analyze_text_features(transcript)

    # Step 4: Build user_responses dynamically
    user_responses = {}

    if any(word in transcript.lower() for word in ["risk", "market", "down", "fall", "crash", "loss"]):
        user_responses["sensex_down_20"] = {
            "emotion": "stress",
            "intensity": 0.8
        }

    if any(word in transcript.lower() for word in ["lockin", "term", "period", "long", "duration", "retirement"]):
        user_responses["lockin_period"] = {
            "emotion": "hesitation",
            "intensity": 0.7
        }

    # Fallback to confidence if nothing matches
    if not user_responses:
        user_responses["generic"] = {
            "emotion": "confidence",
            "intensity": 0.5
        }

    # Step 5: Risk Profiling
    risk_result = calculate_risk_profile(user_responses, voice_emotion=voice_emotion)

    return {
        "transcript": transcript,
        "nlp_analysis": nlp_analysis,
        "audio_features": features,
        "risk_profile": risk_result
    }

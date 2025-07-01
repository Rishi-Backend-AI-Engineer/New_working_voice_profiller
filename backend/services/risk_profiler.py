from data.risk_model import EMOTION_WEIGHTS, RISK_DIMENSIONS
from datetime import datetime
from flask import jsonify, request
from services.risk_model import RISK_DIMENSIONS, EMOTION_WEIGHTS

# Emotion weight multipliers for risk scoring
VOICE_EMOTION_BOOSTS = {
    "fearful": 2.0,
    "angry": 1.5,
    "sad": 1.0,
    "neutral": 0.0,
    "calm": -0.5,
    "happy": -1.0,
    "surprised": 0.5,
    "disgust": 1.0
}

def score_response(emotion, intensity):
    return EMOTION_WEIGHTS.get(emotion.lower(), 0.0) * intensity

def calculate_risk_profile(nlp_result, voice_emotion=None):
    transcript = nlp_result.get("transcript", "").lower()
    sentiment_score = nlp_result.get("sentiment", {}).get("compound", 0.0)
    intents = [i.lower() for i in nlp_result.get("intents", [])]

    user_responses = {}

    # Match triggers from transcript or intents
    for dim, meta in RISK_DIMENSIONS.items():
        for trig in meta["triggers"]:
            trig_lower = trig.lower()

            if trig_lower in transcript or any(trig_lower in i for i in intents):
                emotion = "stress" if "risk" in trig_lower or "loss" in trig_lower else "confidence"
                intensity = abs(sentiment_score) if sentiment_score != 0 else 0.5

                user_responses[trig_lower] = {
                    "emotion": emotion,
                    "intensity": intensity
                }

    total_score = 0.0
    details = []

    for dim, meta in RISK_DIMENSIONS.items():
        dim_score, count = 0.0, 0
        for trig in meta["triggers"]:
            trig_lower = trig.lower()
            if trig_lower in user_responses:
                emotion = user_responses[trig_lower]["emotion"]
                intensity = user_responses[trig_lower]["intensity"]
                dim_score += score_response(emotion, intensity)
                count += 1

        avg = (dim_score / count) if count else 0.0
        weighted = avg * meta["weight"]
        total_score += weighted
        details.append({
            "dimension": dim,
            "avg": round(avg, 3),
            "weighted": round(weighted, 3)
        })

    # Apply voice emotion influence
    if voice_emotion:
        voice_label = voice_emotion.get("label", "").lower()
        voice_boost = VOICE_EMOTION_BOOSTS.get(voice_label, 0.0)
        total_score += voice_boost

    final_score = round(5 + total_score, 2)
    category = (
        "Conservative" if final_score < 4
        else "Aggressive" if final_score > 6
        else "Moderate"
    )

    return {
        "risk_score": final_score,
        "risk_category": category,
        "breakdown": details
    }

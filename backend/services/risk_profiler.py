from data.risk_model import EMOTION_WEIGHTS, RISK_DIMENSIONS
from datetime import datetime
from flask import jsonify, request

def score_response(emotion, intensity):
    return EMOTION_WEIGHTS.get(emotion.lower(), 0) * intensity

def calculate_risk_profile(user_responses):
    total_score = 0
    details = []

    for dim, meta in RISK_DIMENSIONS.items():
        dim_score, count = 0, 0
        for trig in meta["triggers"]:
            if trig in user_responses:
                emotion = user_responses[trig]["emotion"]
                intensity = user_responses[trig]["intensity"]
                dim_score += score_response(emotion, intensity)
                count += 1
        avg = (dim_score / count) if count else 0
        weighted = avg * meta["weight"]
        total_score += weighted
        details.append({"dimension": dim, "avg": avg, "weighted": weighted})

    return {
        "risk_score": round(5 + total_score, 2),
        "risk_category": ("Conservative" if total_score < -1 else "Aggressive" if total_score > 1 else "Moderate"),
        "breakdown": details
    }

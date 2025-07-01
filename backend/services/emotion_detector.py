# services/emotion_detector.py

import torch
import torchaudio
import numpy as np
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
from scipy.special import softmax
import os

# Default local path if env var not set
MODEL_NAME = os.getenv("MODEL_NAME", "./models/emotion")

EMOTION_LABELS = ['angry', 'calm', 'disgust', 'fearful', 'happy', 'neutral', 'sad', 'surprised']
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Global lazy-loaded objects
model = None
extractor = None

def preload_model():
    global model, extractor
    if model is None or extractor is None:
        print(f"⏬ Loading emotion model from: {MODEL_NAME}")
        model = Wav2Vec2ForSequenceClassification.from_pretrained(MODEL_NAME, local_files_only=True).to(DEVICE)
        extractor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_NAME, local_files_only=True)
        print("✅ Emotion model loaded (offline mode).")

def detect_emotion(audio_path):
    if model is None or extractor is None:
        preload_model()

    waveform, sr = torchaudio.load(audio_path)
    waveform = waveform.mean(dim=0).unsqueeze(0)  # Convert to mono

    if sr != 16000:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
        waveform = resampler(waveform)

    inputs = extractor(waveform.squeeze().numpy(), sampling_rate=16000, return_tensors="pt", padding=True)
    with torch.no_grad():
        logits = model(**inputs.to(DEVICE)).logits

    probs = softmax(logits.cpu().numpy()[0])
    top_idx = np.argmax(probs)

    return {
        "label": EMOTION_LABELS[top_idx],
        "score": float(probs[top_idx])
    }

# services/audio_features.py

import numpy as np
import librosa

def extract_audio_features(audio_data):
    y = audio_data["audio"]
    sr = audio_data["sample_rate"]

    features = {
        "duration": librosa.get_duration(y=y, sr=sr),
        "rms": float(np.mean(librosa.feature.rms(y=y))),
        "zcr": float(np.mean(librosa.feature.zero_crossing_rate(y))),
        "spectral_centroid": float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))),
        "spectral_rolloff": float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))),
        "mfcc": np.mean(librosa.feature.mfcc(y=y, sr=sr), axis=1).tolist(),
    }

    return features

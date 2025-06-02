import io
import soundfile as sf
import numpy as np
import librosa

def preprocess_audio(binary_data):
    """Convert binary WAV data to audio time series and sample rate."""
    audio_buffer = io.BytesIO(binary_data)
    audio, sample_rate = sf.read(audio_buffer)

    # Convert to mono if stereo
    if len(audio.shape) > 1:
        audio = np.mean(audio, axis=1)

    return {"audio": audio, "sample_rate": sample_rate}

def compute_rhythm_features(audio, beat_frames, sample_rate):
    return {"num_beats": int(len(beat_frames))}

def extract_voice_quality(audio, sample_rate):
    # Placeholder: implement jitter/shimmer/NAQ/HNR as needed
    return {"quality_metric": "placeholder"}

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
            "mfcc": mfccs,
            "delta_mfcc": delta_mfccs,
            "delta2_mfcc": delta2_mfccs
        }

    if "spectral" in feature_types:
        features["spectral"] = {
            "centroid": librosa.feature.spectral_centroid(y=audio, sr=sample_rate),
            "bandwidth": librosa.feature.spectral_bandwidth(y=audio, sr=sample_rate),
            "rolloff": librosa.feature.spectral_rolloff(y=audio, sr=sample_rate),
            "contrast": librosa.feature.spectral_contrast(y=audio, sr=sample_rate)
        }

    if "prosodic" in feature_types:
        try:
            f0, voiced_flag, voiced_probs = librosa.pyin(audio, fmin=75, fmax=400)
        except Exception as e:
            print(f"[WARN] librosa.pyin() failed: {e}")
            f0, voiced_flag, voiced_probs = np.array([]), np.array([]), np.array([])

        tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sample_rate)
        features["prosodic"] = {
            "f0": f0.tolist(),
            "voiced_flag": voiced_flag.tolist(),
            "voiced_probs": voiced_probs.tolist(),
            "tempo": tempo,
            "rhythm": compute_rhythm_features(audio, beat_frames, sample_rate)
        }

    if "voice_quality" in feature_types:
        features["voice_quality"] = extract_voice_quality(audio, sample_rate)

    return features

def features_summary(features):
    def summarize(arr):
        arr = np.array(arr)
        return {
            "mean": float(np.nanmean(arr)),
            "std": float(np.nanstd(arr)),
            "min": float(np.nanmin(arr)),
            "max": float(np.nanmax(arr))
        }

    summary = {}
    for group, feats in features.items():
        summary[group] = {}
        for key, val in feats.items():
            if isinstance(val, (np.ndarray, list)):
                summary[group][key] = summarize(val)
            else:
                summary[group][key] = val
    return summary

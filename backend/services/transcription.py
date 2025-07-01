# services/transcription.py

import os
import tempfile
from faster_whisper import WhisperModel

# Load model once globally (choose: tiny, base, small, medium, large-v2)
model_size = "base"
model = WhisperModel(model_size, compute_type="int8", cpu_threads=2)

def transcribe_audio(audio_bytes):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name

    try:
        segments, info = model.transcribe(temp_audio_path)

        transcript_segments = []
        full_text = ""
        for seg in segments:
            start = seg.start
            end = seg.end
            text = seg.text.strip()
            full_text += text + " "
            transcript_segments.append({
                "start": start,
                "end": end,
                "text": text
            })

        return {
            "transcript": full_text.strip(),
            "segments": transcript_segments,
            "language": info.language
        }

    except Exception as e:
        print("❌ Error during transcription:", str(e))
        return {"error": str(e)}

    finally:
        os.remove(temp_audio_path)

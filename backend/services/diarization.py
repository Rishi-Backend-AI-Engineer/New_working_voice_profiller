import os
import tempfile
from pyannote.audio import Pipeline, Inference
from pyannote.core import Segment
from sklearn.cluster import SpectralClustering
from sklearn.metrics.pairwise import cosine_similarity
import torch
import soundfile as sf
from pydub import AudioSegment

def audio_separation(input_path: str) -> str:
    # Load Hugging Face token
    from dotenv import load_dotenv
    load_dotenv()
    hf_token = os.getenv("HF_TOKEN")

    # Step 1: Run VAD
    vad_pipeline = Pipeline.from_pretrained("pyannote/voice-activity-detection", use_auth_token=hf_token)
    vad_pipeline.to(torch.device("cpu"))
    vad = vad_pipeline(input_path)

    # Step 2: Load embedding model
    inference = Inference("pyannote/embedding", use_auth_token=hf_token)
    inference.to(torch.device("cpu"))

    # Get audio duration
    with sf.SoundFile(input_path) as f:
        duration = len(f) / f.samplerate

    embeddings = []
    segments = []

    for segment in vad.itersegments():
        start = segment.start
        end = min(segment.end, duration - 0.01)
        if end - start < 0.1:
            continue
        seg = Segment(start, end)
        emb = inference.crop(input_path, seg)
        embeddings.append(torch.tensor(emb.data.mean(axis=0)))
        segments.append(seg)

    X = torch.stack(embeddings).numpy()
    labels = SpectralClustering(n_clusters=2, affinity='precomputed').fit_predict(cosine_similarity(X))

    # Load original audio
    audio = AudioSegment.from_wav(input_path)
    speaker_1 = AudioSegment.empty()

    for seg, label in zip(segments, labels):
        if label == 1:  # Only keep speaker 1 for this example
            start_ms = int(seg.start * 1000)
            end_ms = int(seg.end * 1000)
            speaker_1 += audio[start_ms:end_ms]

    # Save speaker 0 audio as diarized output
    output_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    speaker_1.export(output_temp.name, format="wav")

    return output_temp.name

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
    first_speaker_label = labels[0]  # label of the first speaking segment
    first_speaker_label=1-first_speaker_label
    # Create an empty audio segment for that speaker
    first_speaker_audio = AudioSegment.empty()

    # Collect all segments spoken by the first speaker
    for seg, label in zip(segments, labels):
        if label == first_speaker_label:
            start_ms = int(seg.start * 1000)
            end_ms = int(seg.end * 1000)
            first_speaker_audio += audio[start_ms:end_ms]

    # Save to a temp file
    output_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    first_speaker_audio.export(output_temp.name, format="wav")

    # Return path to output file
    return output_temp.name

    

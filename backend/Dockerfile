# Use a slim Python base image
FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    gcc \
    python3-dev \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir torch==1.10.0 torchaudio==0.10.0 -f https://download.pytorch.org/whl/cpu/torch_stable.html
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -c "\
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor; \
model = Wav2Vec2ForSequenceClassification.from_pretrained('ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition'); \
model.save_pretrained('./models/emotion'); \
extractor = Wav2Vec2FeatureExtractor.from_pretrained('ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition'); \
extractor.save_pretrained('./models/emotion')"

RUN mkdir -p uploads /tmp/numba_cache

RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

ENV PYTHONUNBUFFERED=1
ENV NUMBA_CACHE_DIR=/tmp/numba_cache
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV TOKENIZERS_PARALLELISM=false

EXPOSE 5000

CMD ["gunicorn", "--workers=1", "--bind=0.0.0.0:5000", "--timeout=600", "--max-requests=10", "--max-requests-jitter=2", "app:app"]
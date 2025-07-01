from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor

model = Wav2Vec2ForSequenceClassification.from_pretrained("ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition")
extractor = Wav2Vec2FeatureExtractor.from_pretrained("ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition")

model.save_pretrained("./hf_models/emotion_model")
extractor.save_pretrained("./hf_models/emotion_model")

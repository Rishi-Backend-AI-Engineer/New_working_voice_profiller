# services/nlp_analysis.py

import re
from textblob import TextBlob
import nltk
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

# Make sure these are downloaded at least once
nltk.download("punkt")
nltk.download("stopwords")

from nltk.corpus import stopwords

STOPWORDS = set(stopwords.words("english"))

intent_keywords = {
    "investment": ["invest", "returns", "portfolio", "stocks", "equity", "risk", "sip"],
    "insurance": ["term plan", "policy", "cover", "premium"],
    "retirement": ["pension", "retire", "later", "corpus", "EPF", "PF", "future"],
    "expenses": ["bills", "spending", "monthly", "expenses", "emi", "budget"],
    "savings": ["save", "saving", "deposit", "recurring", "fd", "rd"]
}


def clean_text(text):
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    text = text.lower()
    tokens = [t for t in text.split() if t not in STOPWORDS]
    return " ".join(tokens)


def detect_intent(text):
    tokens = text.split()
    detected = []
    for intent, keywords in intent_keywords.items():
        if any(word in tokens for word in keywords):
            detected.append(intent)
    return detected if detected else ["general"]


def analyze_text_features(transcript):
    cleaned = clean_text(transcript)

    blob = TextBlob(cleaned)
    sentiment = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    word_freq = dict(Counter(cleaned.split()).most_common(10))

    tfidf = TfidfVectorizer(max_features=5)
    tfidf_matrix = tfidf.fit_transform([cleaned])
    tfidf_keywords = tfidf.get_feature_names_out().tolist()

    return {
        "cleaned_text": cleaned,
        "sentiment": {
            "polarity": round(sentiment, 3),
            "subjectivity": round(subjectivity, 3)
        },
        "top_words": word_freq,
        "tfidf_keywords": tfidf_keywords,
        "intent_labels": detect_intent(cleaned)
    }

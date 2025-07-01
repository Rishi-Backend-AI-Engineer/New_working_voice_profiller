from fpdf import FPDF
import io
import re

# Helper to strip emojis & non-ASCII Unicode
def remove_emojis(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Voice-Based Risk Profile Report", 0, 1, "C")
        self.ln(5)

    def section_title(self, title):
        self.set_font("Arial", "B", 12)
        self.set_text_color(0)
        self.cell(0, 10, remove_emojis(title), 0, 1)
        self.ln(1)

    def section_body(self, text):
        self.set_font("Arial", "", 11)
        self.multi_cell(0, 8, remove_emojis(text))
        self.ln()

def generate_pdf(session_doc, filename="session"):
    pdf = PDF()
    pdf.add_page()

    pdf.section_title(f"📄 Session Report: {filename}")
    timestamp = session_doc.get("timestamp")
    if timestamp:
        pdf.section_body(f"Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    # 🗣️ Emotion Detected
    emotion_data = session_doc.get("voice_emotion", {})
    label = emotion_data.get("label", "N/A")
    score = emotion_data.get("score", "N/A")
    pdf.section_title("🗣️ Detected Emotion from Voice")
    pdf.section_body(f"Dominant Emotion: {str(label).capitalize()} (Confidence: {round(score, 2) if isinstance(score, (int, float)) else score})")

    # 💬 Transcript
    pdf.section_title("💬 Transcript")
    pdf.section_body(session_doc.get("transcript", "N/A"))

    # 🧠 NLP Analysis
    nlp = session_doc.get("nlp_analysis", {})
    pdf.section_title("🧠 Text Analysis")
    pdf.section_body(f"- Sentiment Polarity: {nlp.get('sentiment', {}).get('polarity', 'N/A')}")
    pdf.section_body(f"- Subjectivity: {nlp.get('sentiment', {}).get('subjectivity', 'N/A')}")
    pdf.section_body(f"- Detected Intents: {', '.join(nlp.get('intent_labels', []))}")
    pdf.section_body(f"- TF-IDF Keywords: {', '.join(nlp.get('tfidf_keywords', []))}")

    # 🎧 Audio Features
    audio = session_doc.get("audio_features", {}).get("summary", {})
    pdf.section_title("🎧 Audio Features Summary")
    for k, v in audio.items():
        pdf.section_body(f"- {k.replace('_', ' ').title()}: {v}")

    # 📉 Risk Profile
    risk = session_doc.get("risk_profile", {})
    pdf.section_title("📉 Risk Profile")
    pdf.section_body(f"- Risk Score: {risk.get('risk_score')}")
    pdf.section_body(f"- Category: {risk.get('risk_category')}")

    # 📊 Risk Breakdown
    pdf.section_title("📊 Risk Breakdown")
    for dim in risk.get("breakdown", []):
        dimension = dim.get("dimension", "Unknown").replace("_", " ").title()
        weight = round(dim.get("weighted", 0.0), 3)
        pdf.section_body(f"- {dimension} → Weighted: {weight}")

    # 🎯 Recommendations
    pdf.section_title("🎯 Recommendations")
    for rec in session_doc.get("recommendations", []):
        pdf.section_body(f"- {rec}")

    # ✅ Output to BytesIO
    pdf_output = io.BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output

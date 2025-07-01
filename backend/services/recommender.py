# services/recommender.py

def generate_recommendations(risk_profile, nlp_analysis):
    category = risk_profile.get("risk_category", "Moderate")
    intents = nlp_analysis.get("intent_labels") or nlp_analysis.get("intents", [])
    sentiment = nlp_analysis.get("sentiment", {}).get("polarity", 0)

    recs = []

    # Base on risk
    if category == "Conservative":
        recs.append("📉 Consider debt mutual funds or fixed deposits for capital protection.")
        recs.append("🛡️ Insurance coverage and emergency fund should be top priority.")
    elif category == "Moderate":
        recs.append("⚖️ Balanced mutual funds and large-cap equity could suit your profile.")
        recs.append("📊 Diversify across equity and debt instruments.")
    else:
        recs.append("🚀 High-growth opportunities like small/mid-cap equity may fit.")
        recs.append("📈 SIPs in aggressive mutual funds could be explored.")

    # Based on detected intent
    if "insurance" in intents:
        recs.append("🩺 Review your term insurance and health cover.")
    if "investment" in intents:
        recs.append("💰 Build a SIP or ELSS investment plan aligned to your goals.")
    if "retirement" in intents:
        recs.append("⏳ Start retirement planning early with NPS or pension funds.")
    if "savings" in intents:
        recs.append("💳 Setup automated recurring deposits for disciplined savings.")
    if "expenses" in intents:
        recs.append("📉 Consider budgeting tools to track and cut down expenses.")

    # Sentiment nudges
    if sentiment < -0.3:
        recs.append("💡 Consider speaking to a financial advisor to ease your concerns.")
    elif sentiment > 0.4:
        recs.append("🔥 You're feeling confident — use that to kickstart your investment journey!")

    return recs

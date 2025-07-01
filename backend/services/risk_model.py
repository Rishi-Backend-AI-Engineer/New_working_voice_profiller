# services/risk_model.py

EMOTION_WEIGHTS = {
    "stress": 1.2,
    "hesitation": 0.9,
    "confidence": -0.8,
    "fear": 1.5,
    "trust": -1.0,
    "neutral": 0.0,
}

RISK_DIMENSIONS = {
    "Time Horizon": {
        "weight": 1.2,
        "triggers": [
            "retirement", "long term", "future", "years from now",
            "planning ahead", "in 10 years", "post retirement",
            "after 60", "savings for later", "long haul"
        ]
    },
    "Income Vs Growth": {
        "weight": 1.1,
        "triggers": [
            "mutual funds", "capital appreciation", "growth", "equity",
            "stocks", "share market", "returns", "small cap", "mid cap",
            "index fund", "invest for profit"
        ]
    },
    "Risk Appetite": {
        "weight": 1.4,
        "triggers": [
            "risk", "market crash", "volatility", "nifty down", "sensex down",
            "high risk", "fluctuating", "investing in crypto", "nervous",
            "worried", "anxious", "scared", "tension", "unstable"
        ]
    },
    "Liquidity Needs": {
        "weight": 1.0,
        "triggers": [
            "emergency", "urgent money", "withdraw anytime", "no lock-in",
            "immediate cash", "liquidity", "quick access", "short term",
            "available funds", "cash in hand", "need money soon"
        ]
    },
    "Tax Consideration": {
        "weight": 0.8,
        "triggers": [
            "tax saving", "section 80c", "tax benefit", "deductions",
            "tax efficient", "elss", "ppf", "nps", "income tax", "reduce taxes"
        ]
    },
    "Financial Goals": {
        "weight": 1.3,
        "triggers": [
            "child education", "marriage", "buy a house", "vacation", "car",
            "goal based", "saving for wedding", "dream home", "travel fund",
            "property", "future goals", "college fees", "house deposit"
        ]
    }
}

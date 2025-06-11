EMOTION_WEIGHTS = {
    "stress": -2, "fear": -2, "anxiety": -2, "sadness": -1, "hesitation": -1,
    "neutral": 0, "confidence": 2, "assertiveness": 2, "excitement": 1, "resignation": 0
}

RISK_DIMENSIONS = {
    "market_risk": {"weight": 0.2, "triggers": ["sensex_down_20", "market_down_18_months"]},
    "liquidity_risk": {"weight": 0.15, "triggers": ["lockin_period", "illiquid_investments"]},
    "loss_aversion": {"weight": 0.2, "triggers": ["loss_vs_gain", "negative_emotions"]},
    "time_horizon": {"weight": 0.15, "triggers": ["delayed_gratification"]},
    "income_vs_growth": {"weight": 0.15, "triggers": ["growth_strategies"]},
    "india_specific": {"weight": 0.15, "triggers": ["gold_real_estate", "digital_investing"]}
}

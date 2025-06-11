def recommend_strategy(age, risk_score):
    if age < 30 and risk_score > 6:
        return ["SIP Growth Fund", "ELSS", "NPS"]
    elif age > 50 and risk_score < 5:
        return ["Debt MF", "SWP", "Health Insurance"]
    else:
        return ["Balanced Fund", "Gold ETF", "Hybrid"]
    
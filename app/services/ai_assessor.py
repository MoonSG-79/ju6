
def ai_score(features: dict, human_score: float, mode: str = "Normal") -> float:
    r = max(0.0, min(1.0, human_score/100.0))
    vol = features.get("volatility", 0.02)
    spr = features.get("spread", 0.2)
    mom = features.get("momentum", 0.5)
    trd = features.get("trend", 0.5)

    risk_penalty = (vol*2 + spr*0.5)
    pos_bonus    = (mom*0.7 + trd*0.7)

    if mode.lower().startswith("cons"):
        w_risk, w_pos = 1.4, 0.8
    elif mode.lower().startswith("agg"):
        w_risk, w_pos = 0.7, 1.3
    else:
        w_risk, w_pos = 1.0, 1.0

    score = max(0.0, min(1.0, 0.4*r + 0.6*(w_pos*pos_bonus - w_risk*risk_penalty + 0.5)))
    return round(score*100, 2)

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class RiskInput(BaseModel):
    language_risk: str
    link_risk: str
    from_address: str

@app.post("/verdict")
def final_verdict(data: RiskInput):
    score = 0
    if data.language_risk == "high":
        score += 0.6
    if data.link_risk == "medium":
        score += 0.3
    return {
        "phishing_score": round(score, 2),
        "risk_level": "ALTO" if score >= 0.6 else "BAIXO",
        "recommendation": "Bloquear e marcar como phishing" if score >= 0.6 else "Seguro"
    }
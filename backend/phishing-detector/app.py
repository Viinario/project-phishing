from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

class TextInput(BaseModel):
    text: str

@app.post("/detect")
def detect_phishing(data: TextInput):
    # Simula a resposta de um LLM
    if "bloqueio" in data.text.lower():
        return {
            "risk": "high",
            "explanation": "Palavras de urgência detectadas."
        }
    return {
        "risk": "low",
        "explanation": "Sem indicação de phishing."
    }
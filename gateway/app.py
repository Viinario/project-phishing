from fastapi import FastAPI, Request
from pydantic import BaseModel
import requests

app = FastAPI()

class EmailInput(BaseModel):
    subject: str
    body: str
    from_address: str

@app.post("/analyze")
def analyze_email(data: EmailInput):
    email_response = requests.post('http://email-parser:5000/parse', json=data.dict())
    email_result = email_response.json()

    link_response = requests.post('http://link-analyzer:5000/analyze', json={"links": email_result.get("links", [])})
    link_result = link_response.json()

    verdict_payload = {
        'language_risk': 'high' if email_result.get('text', '').lower().find('bloqueio') != -1 else 'low',
        'link_risk': 'medium' if link_result.get('suspicious_links') else 'low',
        'from_address': email_result.get('sender')
    }

    verdict_response = requests.post('http://verdict-service:5000/verdict', json=verdict_payload)
    return verdict_response.json()

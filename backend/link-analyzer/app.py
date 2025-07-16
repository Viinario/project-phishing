from fastapi import FastAPI
from pydantic import BaseModel
import re
from typing import List

app = FastAPI()

class LinksInput(BaseModel):
    links: List[str]

@app.post("/analyze")
def analyze_links(data: LinksInput):
    suspicious = [link for link in data.links if "bad" in link]
    return {
        "suspicious_links": suspicious,
        "domain_reputation": "unknown"
    }

from fastapi import FastAPI, Request
from pydantic import BaseModel
import re
from typing import List

app = FastAPI()

class EmailInput(BaseModel):
    subject: str
    body: str
    from_address: str

@app.post("/parse")
def parse_email(data: EmailInput):
    links = re.findall(r"https?://\S+", data.body)
    text = re.sub(r"https?://\S+", "", data.body)
    return {
        "sender": data.from_address,
        "links": links,
        "text": text.strip()
    }
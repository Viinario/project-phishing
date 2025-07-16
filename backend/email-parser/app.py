from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import re
import email
from email.message import EmailMessage
from typing import List, Optional
import io

app = FastAPI()

class EmailData(BaseModel):
    subject: str
    body: str
    sender: str
    links: List[str]
    text_content: str

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "email-parser"}

@app.post("/parse-eml")
async def parse_eml_file(file: UploadFile = File(...)):
    """Extrai conteúdo de um arquivo EML"""
    try:
        # Lê o conteúdo do arquivo
        contents = await file.read()
        
        # Parse do email
        msg = email.message_from_bytes(contents)
        
        # Extrai informações básicas
        subject = msg.get('Subject', '')
        sender = msg.get('From', '')
        
        # Extrai o corpo do email
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif part.get_content_type() == "text/html":
                    # Para HTML, vamos extrair texto simples (pode melhorar com BeautifulSoup)
                    html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    body += re.sub(r'<[^>]+>', '', html_content)
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        # Extrai links do corpo do email
        links = re.findall(r'https?://[^\s<>"]+', body)
        
        # Remove links do texto para análise limpa
        text_content = re.sub(r'https?://[^\s<>"]+', '', body).strip()
        
        return {
            "subject": subject,
            "body": body,
            "sender": sender,
            "links": links,
            "text_content": text_content
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo EML: {str(e)}")

@app.post("/parse")
def parse_email_data(data: dict):
    """Endpoint para dados de email já extraídos (mantido para compatibilidade)"""
    subject = data.get('subject', '')
    body = data.get('body', '')
    sender = data.get('from_address', '')
    
    # Extrai links do corpo do email
    links = re.findall(r'https?://[^\s<>"]+', body)
    
    # Remove links do texto para análise limpa
    text_content = re.sub(r'https?://[^\s<>"]+', '', body).strip()
    
    return {
        "subject": subject,
        "body": body,
        "sender": sender,
        "links": links,
        "text_content": text_content
    }
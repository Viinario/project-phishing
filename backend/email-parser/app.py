from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import re
import email
from email.message import EmailMessage
from typing import List, Optional, Dict, Any
import io
import os
import google.generativeai as genai
import json
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da API do Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY não encontrada! Defina a variável de ambiente.")
    raise ValueError("GEMINI_API_KEY é obrigatória")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

app = FastAPI()

class EmailData(BaseModel):
    subject: str
    body: str
    sender: str
    links: List[str]
    text_content: str
    ai_analysis: Optional[Dict[str, Any]] = None

def analyze_email_with_ai(email_content: str, headers: Dict[str, str]) -> Dict[str, Any]:
    """Analisa o email usando IA para extrair informações e detectar características suspeitas"""
    try:
        prompt = f"""
        Analise este email e forneça uma análise detalhada em formato JSON. 
        
        HEADERS DO EMAIL:
        {json.dumps(headers, indent=2, ensure_ascii=False)}
        
        CONTEÚDO DO EMAIL:
        {email_content}
        
        Por favor, analise e retorne um JSON com:
        1. "extracted_fields": {{
            "sender_analysis": "Análise do remetente (legitimidade, spoofing, etc)",
            "subject_analysis": "Análise do assunto (características suspeitas)",
            "body_analysis": "Análise do corpo do email",
            "headers_analysis": "Análise dos headers técnicos"
        }}
        2. "suspicious_indicators": [lista de indicadores suspeitos encontrados]
        3. "technical_details": {{
            "encoding_issues": "Problemas de codificação detectados",
            "spoofing_signs": "Sinais de spoofing de domínio",
            "header_inconsistencies": "Inconsistências nos headers"
        }}
        4. "extraction_confidence": score de 0-100 da confiança na extração
        5. "phishing_indicators": [lista específica de indicadores de phishing]
        
        Responda APENAS com o JSON válido, sem explicações adicionais.
        """
        
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        
        return {
            "ai_analysis_successful": True,
            "analysis": result
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar resposta da IA: {e}")
        return {
            "ai_analysis_successful": False,
            "error": "Erro ao processar resposta da IA",
            "raw_response": response.text if 'response' in locals() else "N/A"
        }
    except Exception as e:
        logger.error(f"Erro na análise com IA: {e}")
        return {
            "ai_analysis_successful": False,
            "error": str(e)
        }

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "email-parser", "ai_enabled": GEMINI_API_KEY is not None}

@app.post("/parse-eml")
async def parse_eml_file(file: UploadFile = File(...)):
    """Extrai conteúdo de um arquivo EML usando IA para análise avançada"""
    try:
        # Lê o conteúdo do arquivo
        contents = await file.read()
        
        # Parse do email
        msg = email.message_from_bytes(contents)
        
        # Extrai informações básicas
        subject = msg.get('Subject', '')
        sender = msg.get('From', '')
        
        # Coleta headers importantes para análise
        headers = {
            'From': msg.get('From', ''),
            'To': msg.get('To', ''),
            'Subject': msg.get('Subject', ''),
            'Date': msg.get('Date', ''),
            'Message-ID': msg.get('Message-ID', ''),
            'Return-Path': msg.get('Return-Path', ''),
            'Reply-To': msg.get('Reply-To', ''),
            'X-Originating-IP': msg.get('X-Originating-IP', ''),
            'X-Mailer': msg.get('X-Mailer', ''),
            'Content-Type': msg.get('Content-Type', ''),
            'Authentication-Results': msg.get('Authentication-Results', ''),
            'DKIM-Signature': msg.get('DKIM-Signature', ''),
            'SPF': msg.get('Received-SPF', '')
        }
        
        # Extrai o corpo do email
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif part.get_content_type() == "text/html":
                    # Para HTML, vamos extrair texto simples
                    html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    body += re.sub(r'<[^>]+>', '', html_content)
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        # Extrai links do corpo do email (método tradicional como backup)
        links = re.findall(r'https?://[^\s<>"]+', body)
        
        # Remove links do texto para análise limpa
        text_content = re.sub(r'https?://[^\s<>"]+', '', body).strip()
        
        # Análise com IA
        full_email_content = f"HEADERS:\n{json.dumps(headers, indent=2)}\n\nBODY:\n{body}"
        ai_analysis = analyze_email_with_ai(full_email_content, headers)
        
        return {
            "subject": subject,
            "body": body,
            "sender": sender,
            "links": links,
            "text_content": text_content,
            "headers": headers,
            "ai_analysis": ai_analysis,
            "extraction_method": "ai_enhanced"
        }
    
    except Exception as e:
        logger.error(f"Erro ao processar arquivo EML: {e}")
        raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo EML: {str(e)}")

@app.post("/parse")
def parse_email_data(data: dict):
    """Endpoint para dados de email já extraídos com análise IA aprimorada"""
    try:
        subject = data.get('subject', '')
        body = data.get('body', '')
        sender = data.get('from_address', data.get('sender', ''))
        
        # Extrai links do corpo do email
        links = re.findall(r'https?://[^\s<>"]+', body)
        
        # Remove links do texto para análise limpa
        text_content = re.sub(r'https?://[^\s<>"]+', '', body).strip()
        
        # Simula headers básicos para dados já extraídos
        headers = {
            'From': sender,
            'Subject': subject,
            'Content-Type': 'text/plain'
        }
        
        # Análise com IA
        full_email_content = f"SUBJECT: {subject}\nSENDER: {sender}\nBODY:\n{body}"
        ai_analysis = analyze_email_with_ai(full_email_content, headers)
        
        return {
            "subject": subject,
            "body": body,
            "sender": sender,
            "links": links,
            "text_content": text_content,
            "headers": headers,
            "ai_analysis": ai_analysis,
            "extraction_method": "ai_enhanced_data"
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar dados do email: {e}")
        raise HTTPException(status_code=400, detail=f"Erro ao processar dados do email: {str(e)}")
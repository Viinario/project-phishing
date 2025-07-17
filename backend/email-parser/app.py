from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import re
import email
from email.message import EmailMessage
from typing import List, Optional, Dict, Any
import io
import os
import json
import logging
import requests

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class EmailData(BaseModel):
    subject: str
    body: str
    from_address: str
    links: List[str]

def extract_email_data_with_ai(email_content: str, headers: Dict[str, str]) -> Dict[str, Any]:
    """Usa IA para extrair dados básicos do email (subject, body, sender) de forma mais precisa"""
    
    # Verifica se a API key está configurada
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'cole_sua_chave_api_do_gemini_aqui':
        logger.error("GEMINI_API_KEY não configurada")
        return {
            "ai_extraction_successful": False,
            "error": "GEMINI_API_KEY não configurada"
        }
    
    try:
        prompt = f"""
        Analise este email e extraia as informações básicas de forma precisa.
        
        HEADERS DO EMAIL:
        {json.dumps(headers, indent=2, ensure_ascii=False)}
        
        CONTEÚDO COMPLETO DO EMAIL:
        {email_content}
        
        FORMATO DE RESPOSTA OBRIGATÓRIO:
        
        SUBJECT: [Extraia o assunto exato do email]
        
        FROM_ADDRESS: [Extraia o endereço do remetente real]
        
        BODY_TEXT: [Extraia apenas o corpo da mensagem, removendo headers e metadados]
        
        EXTRACTED_LINKS:
        - [Link 1]
        - [Link 2]
        - [Link 3]
        
        EXTRACTION_CONFIDENCE: [Score de 0-100 da confiança na extração]
        
        NOTES: [Notas sobre problemas de codificação, formatação ou outros detalhes técnicos]
        
        Foque apenas na EXTRAÇÃO precisa dos dados, sem análise de segurança.
        """
        
        # Headers para a API
        headers_api = {
            'Content-Type': 'application/json',
            'x-goog-api-key': api_key
        }
        
        # Payload para a API
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 4096,
            }
        }
        
        timeout = 20
        
        logger.info("Extraindo dados do email com Gemini AI")
        
        response = requests.post(
            'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent',
            headers=headers_api,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code != 200:
            logger.error(f"Erro na API do Gemini: {response.status_code}")
            return {
                "ai_extraction_successful": False,
                "error": f"Erro na API do Gemini: {response.status_code}"
            }
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
            logger.info(f"Resposta do Gemini recebida: {ai_response[:200]}...")
            
            # Parsing manual da resposta estruturada
            extraction = {}
            
            # Extrai subject
            subject_match = re.search(r'SUBJECT:\s*(.+?)(?=\n\n|\nFROM_ADDRESS:|$)', ai_response, re.DOTALL)
            extraction["subject"] = subject_match.group(1).strip() if subject_match else ""
            
            # Extrai from_address
            from_match = re.search(r'FROM_ADDRESS:\s*(.+?)(?=\n\n|\nBODY_TEXT:|$)', ai_response, re.DOTALL)
            extraction["from_address"] = from_match.group(1).strip() if from_match else ""
            
            # Extrai body
            body_match = re.search(r'BODY_TEXT:\s*(.+?)(?=\n\n|\nEXTRACTED_LINKS:|$)', ai_response, re.DOTALL)
            extraction["body"] = body_match.group(1).strip() if body_match else ""
            
            # Extrai links
            links_section = re.search(r'EXTRACTED_LINKS:\s*(.+?)(?=\n\n|\nEXTRACTION_CONFIDENCE:|$)', ai_response, re.DOTALL)
            if links_section:
                links = re.findall(r'-\s*(.+)', links_section.group(1))
                extraction["links"] = [link.strip() for link in links]
            else:
                extraction["links"] = []
            
            # Extrai confidence
            confidence_match = re.search(r'EXTRACTION_CONFIDENCE:\s*(\d+)', ai_response)
            extraction["confidence"] = int(confidence_match.group(1)) if confidence_match else 85
            
            # Extrai notas
            notes_match = re.search(r'NOTES:\s*(.+?)(?=\n\n|$)', ai_response, re.DOTALL)
            extraction["notes"] = notes_match.group(1).strip() if notes_match else "Extração normal"
            
            return {
                "ai_extraction_successful": True,
                "extraction": extraction
            }
        else:
            logger.error("Resposta inválida da API do Gemini")
            return {
                "ai_extraction_successful": False,
                "error": "Resposta inválida da API do Gemini"
            }
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout na API do Gemini após {timeout}s")
        return {
            "ai_extraction_successful": False,
            "error": f"Timeout na API do Gemini após {timeout}s"
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de conexão com API do Gemini: {str(e)}")
        return {
            "ai_extraction_successful": False,
            "error": f"Erro ao conectar com a API do Gemini: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Erro na extração com IA: {e}")
        return {
            "ai_extraction_successful": False,
            "error": str(e)
        }

@app.get("/")
def health_check():
    api_key = os.getenv('GEMINI_API_KEY')
    return {"status": "healthy", "service": "email-parser", "ai_enabled": api_key is not None and api_key != 'cole_sua_chave_api_do_gemini_aqui'}

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
        
        # Análise com IA para melhorar a extração
        full_email_content = f"HEADERS:\n{json.dumps(headers, indent=2)}\n\nBODY:\n{body}"
        ai_extraction = extract_email_data_with_ai(full_email_content, headers)
        
        # Usa dados da IA se disponível, senão usa extração tradicional
        if ai_extraction.get('ai_extraction_successful'):
            extraction_data = ai_extraction['extraction']
            final_subject = extraction_data.get('subject') or subject
            final_body = extraction_data.get('body') or body
            final_sender = extraction_data.get('from_address') or sender
            final_links = extraction_data.get('links') or links
            extraction_method = "ai_enhanced"
        else:
            final_subject = subject
            final_body = body
            final_sender = sender
            final_links = links
            extraction_method = "traditional"
        
        return {
            "subject": final_subject,
            "body": final_body,
            "from_address": final_sender,
            "links": final_links,
            "headers": headers,
            "ai_extraction": ai_extraction,
            "extraction_method": extraction_method
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
        
        # Simula headers básicos para dados já extraídos
        headers = {
            'From': sender,
            'Subject': subject,
            'Content-Type': 'text/plain'
        }
        
        # Análise com IA para melhorar a extração
        full_email_content = f"SUBJECT: {subject}\nSENDER: {sender}\nBODY:\n{body}"
        ai_extraction = extract_email_data_with_ai(full_email_content, headers)
        
        # Usa dados da IA se disponível, senão usa dados fornecidos
        if ai_extraction.get('ai_extraction_successful'):
            extraction_data = ai_extraction['extraction']
            final_subject = extraction_data.get('subject') or subject
            final_body = extraction_data.get('body') or body
            final_sender = extraction_data.get('from_address') or sender
            final_links = extraction_data.get('links') or links
            extraction_method = "ai_enhanced_data"
        else:
            final_subject = subject
            final_body = body
            final_sender = sender
            final_links = links
            extraction_method = "traditional_data"
        
        return {
            "subject": final_subject,
            "body": final_body,
            "from_address": final_sender,
            "links": final_links,
            "headers": headers,
            "ai_extraction": ai_extraction,
            "extraction_method": extraction_method
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar dados do email: {e}")
        raise HTTPException(status_code=400, detail=f"Erro ao processar dados do email: {str(e)}")
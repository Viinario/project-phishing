from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
import json
import logging

app = FastAPI()

# Configuração de logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

class EmailContent(BaseModel):
    subject: str
    body: str
    sender: str

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "phishing-detector"}

@app.post("/analyze")
def analyze_with_gemini(data: EmailContent):
    """Analisa o conteúdo do email usando a API do Google Gemini"""
    
    # Verifica se a API key está configurada
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'cole_sua_chave_api_do_gemini_aqui':
        logger.error("GEMINI_API_KEY não configurada ou usando valor padrão")
        raise HTTPException(
            status_code=500, 
            detail="GEMINI_API_KEY não configurada. Verifique o arquivo .env"
        )
    
    # Monta o prompt para análise
    email_content = f"""
    Assunto: {data.subject}
    Remetente: {data.sender}
    Corpo: {data.body}
    """
    
    prompt = f"Analise se este email é phishing ou não. Responda apenas 'SIM' se for phishing ou 'NÃO' se for legítimo, seguido de uma explicação breve em português: {email_content}"
    
    # Payload para a API do Gemini
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }
    
    # Timeout configurável
    timeout = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    try:
        logger.info(f"Enviando requisição para Gemini API (timeout: {timeout}s)")
        
        # Chama a API do Gemini
        response = requests.post(
            'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent',
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code != 200:
            logger.error(f"Erro na API do Gemini: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail=f"Erro na API do Gemini: {response.status_code}")
        
        result = response.json()
        
        # Extrai a resposta
        if 'candidates' in result and len(result['candidates']) > 0:
            gemini_response = result['candidates'][0]['content']['parts'][0]['text']
            
            logger.info(f"Resposta do Gemini recebida: {gemini_response[:100]}...")
            
            # Determina se é phishing baseado na resposta
            is_phishing = gemini_response.upper().startswith('SIM')
            risk_level = "high" if is_phishing else "low"
            
            return {
                "is_phishing": is_phishing,
                "risk_level": risk_level,
                "explanation": gemini_response,
                "confidence": "high" if "altíssima probabilidade" in gemini_response or "certeza" in gemini_response else "medium"
            }
        else:
            logger.error("Resposta inválida da API do Gemini")
            raise HTTPException(status_code=500, detail="Resposta inválida da API do Gemini")
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout na API do Gemini após {timeout}s")
        raise HTTPException(status_code=504, detail="Timeout na API do Gemini")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de conexão com API do Gemini: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao conectar com a API do Gemini: {str(e)}")
    except Exception as e:
        logger.error(f"Erro interno: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/detect")
def detect_phishing_simple(data: dict):
    """Endpoint simples para detecção (mantido para compatibilidade)"""
    text = data.get('text', '')
    
    # Análise simples baseada em palavras-chave
    phishing_keywords = [
        'bloqueio', 'urgente', 'imediatamente', 'clique aqui', 
        'verificar conta', 'suspensa', 'expirar', 'confirmar dados',
        'atualizar informações', 'ação necessária'
    ]
    
    text_lower = text.lower()
    detected_keywords = [keyword for keyword in phishing_keywords if keyword in text_lower]
    
    if detected_keywords:
        return {
            "risk": "high",
            "explanation": f"Palavras suspeitas detectadas: {', '.join(detected_keywords)}",
            "is_phishing": True
        }
    
    return {
        "risk": "low", 
        "explanation": "Sem indicadores claros de phishing",
        "is_phishing": False
    }
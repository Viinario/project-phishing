from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
import json
import logging
import re

app = FastAPI()

# Configuração de logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

class EmailContent(BaseModel):
    subject: str
    body: str
    from_address: str

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
    
    # Monta o prompt para análise detalhada de phishing
    email_content = f"""
    Assunto: {data.subject}
    Remetente: {data.from_address}
    Corpo: {data.body}
    """
    
    prompt = f"""
    Analise PROFUNDAMENTE se este email é phishing ou não.
    
    EMAIL PARA ANÁLISE:
    {email_content}
    
    FORMATO DE RESPOSTA OBRIGATÓRIO:
    
    IS_PHISHING: [SIM ou NÃO]
    
    RISK_SCORE: [Score de 0-100, onde 100 = phishing certo]
    
    RISK_LEVEL: [critical | high | medium | low]
    
    CONFIDENCE: [high | medium | low]
    
    PHISHING_TECHNIQUES:
    - [Técnica 1 detectada]
    - [Técnica 2 detectada]
    
    SENDER_ANALYSIS: [Análise específica do remetente e domínio]
    
    SUBJECT_ANALYSIS: [Análise específica do assunto]
    
    BODY_ANALYSIS: [Análise específica do corpo da mensagem]
    
    URGENCY_INDICATORS: [Indicadores de urgência artificial]
    
    SOCIAL_ENGINEERING: [Técnicas de engenharia social detectadas]
    
    DETAILED_EXPLANATION: [Explicação detalhada e justificativa da decisão]
    
    Seja específico e técnico na análise.
    """
    
    # Payload para a API do Gemini
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
    
    headers = {
        'Content-Type': 'application/json',
        'x-goog-api-key': api_key
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
        
        # Extrai a resposta e faz parsing estruturado
        if 'candidates' in result and len(result['candidates']) > 0:
            gemini_response = result['candidates'][0]['content']['parts'][0]['text']
            
            logger.info(f"Resposta do Gemini recebida: {gemini_response[:200]}...")
            
            # Parsing estruturado da resposta
            analysis = {}
            
            # Extrai se é phishing
            phishing_match = re.search(r'IS_PHISHING:\s*(SIM|NÃO|YES|NO)', gemini_response, re.IGNORECASE)
            is_phishing = phishing_match and phishing_match.group(1).upper() in ['SIM', 'YES'] if phishing_match else False
            
            # Extrai risk score
            score_match = re.search(r'RISK_SCORE:\s*(\d+)', gemini_response)
            risk_score = int(score_match.group(1)) if score_match else (80 if is_phishing else 20)
            
            # Extrai risk level
            level_match = re.search(r'RISK_LEVEL:\s*(\w+)', gemini_response)
            risk_level = level_match.group(1).lower() if level_match else ("high" if is_phishing else "low")
            
            # Extrai confidence
            confidence_match = re.search(r'CONFIDENCE:\s*(\w+)', gemini_response)
            confidence = confidence_match.group(1).lower() if confidence_match else "medium"
            
            # Extrai técnicas de phishing
            techniques_section = re.search(r'PHISHING_TECHNIQUES:\s*(.+?)(?=\n\n|\nSENDER_ANALYSIS:|$)', gemini_response, re.DOTALL)
            if techniques_section:
                techniques = re.findall(r'-\s*(.+)', techniques_section.group(1))
                analysis["phishing_techniques"] = [tech.strip() for tech in techniques]
            else:
                analysis["phishing_techniques"] = []
            
            # Extrai análises específicas
            sender_match = re.search(r'SENDER_ANALYSIS:\s*(.+?)(?=\n\n|\nSUBJECT_ANALYSIS:|$)', gemini_response, re.DOTALL)
            subject_match = re.search(r'SUBJECT_ANALYSIS:\s*(.+?)(?=\n\n|\nBODY_ANALYSIS:|$)', gemini_response, re.DOTALL)
            body_match = re.search(r'BODY_ANALYSIS:\s*(.+?)(?=\n\n|\nURGENCY_INDICATORS:|$)', gemini_response, re.DOTALL)
            
            analysis["detailed_analysis"] = {
                "sender_analysis": sender_match.group(1).strip() if sender_match else "Análise não disponível",
                "subject_analysis": subject_match.group(1).strip() if subject_match else "Análise não disponível",
                "body_analysis": body_match.group(1).strip() if body_match else "Análise não disponível"
            }
            
            # Extrai explicação detalhada
            explanation_match = re.search(r'DETAILED_EXPLANATION:\s*(.+?)(?=\n\n|$)', gemini_response, re.DOTALL)
            detailed_explanation = explanation_match.group(1).strip() if explanation_match else "Explicação não disponível"
            
            return {
                "is_phishing": is_phishing,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "confidence": confidence,
                "phishing_techniques": analysis["phishing_techniques"],
                "detailed_analysis": analysis["detailed_analysis"],
                "explanation": detailed_explanation,
                "raw_response": gemini_response[:500] + "..." if len(gemini_response) > 500 else gemini_response
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
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import requests
from urllib.parse import urlparse
from typing import List
import os
import logging

app = FastAPI()

# Configuração de logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

class LinksInput(BaseModel):
    links: List[str]

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "link-analyzer"}

def analyze_links_with_ai(urls: List[str]) -> dict:
    """Analisa URLs usando exclusivamente a IA do Google Gemini"""
    
    # Verifica se a API key está configurada
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'cole_sua_chave_api_do_gemini_aqui':
        logger.error("GEMINI_API_KEY não configurada")
        raise HTTPException(
            status_code=500, 
            detail="GEMINI_API_KEY não configurada. Verifique o arquivo .env"
        )
    
    # Prepara o prompt para análise
    urls_text = "\n".join([f"{i+1}. {url}" for i, url in enumerate(urls)])
    
    prompt = f"""
    Analise estas URLs em busca de indicadores de phishing, malware ou outros riscos de segurança:
    
    {urls_text}
    
    Para cada URL, avalie:
    1. É suspeita/maliciosa? (SIM/NÃO)
    2. Nível de risco (CRÍTICO/ALTO/MÉDIO/BAIXO)
    3. Razões específicas (domínio falso, typosquatting, URL encurtada suspeita, etc.)
    
    Responda OBRIGATORIAMENTE neste formato exato:
    SCORE_GERAL: [número de 0 a 100]
    URLS_SUSPEITAS:
    [liste apenas as URLs suspeitas, uma por linha, sem numeração]
    EXPLICAÇÃO:
    [explicação detalhada em português dos riscos encontrados]
    """
    
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
    
    timeout = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    try:
        logger.info(f"Analisando {len(urls)} URLs com Gemini AI")
        
        response = requests.post(
            'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent',
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code != 200:
            logger.error(f"Erro na API do Gemini: {response.status_code}")
            raise HTTPException(status_code=500, detail=f"Erro na API do Gemini: {response.status_code}")
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
            logger.info(f"Resposta do Gemini recebida: {ai_response[:200]}...")
            
            # Extrai o score geral
            score_match = re.search(r'SCORE_GERAL:\s*(\d+)', ai_response)
            overall_score = int(score_match.group(1)) if score_match else 50
            
            # Extrai URLs suspeitas da resposta da IA
            suspicious_urls = []
            lines = ai_response.split('\n')
            capturing_urls = False
            
            for line in lines:
                line = line.strip()
                if 'URLS_SUSPEITAS:' in line:
                    capturing_urls = True
                    continue
                elif capturing_urls and 'EXPLICAÇÃO:' in line:
                    break
                elif capturing_urls and line and ('http' in line or 'www.' in line):
                    # Extrai a URL da linha
                    url_match = re.search(r'https?://[^\s]+', line)
                    if url_match:
                        suspicious_urls.append(url_match.group())
                    # Também tenta encontrar URLs sem protocolo
                    elif 'www.' in line:
                        www_match = re.search(r'www\.[^\s]+', line)
                        if www_match:
                            suspicious_urls.append('https://' + www_match.group())
            
            # Determina nível de risco baseado no score
            if overall_score >= 80:
                risk_level = "critical"
            elif overall_score >= 60:
                risk_level = "high"
            elif overall_score >= 30:
                risk_level = "medium"
            else:
                risk_level = "low"
                
            return {
                "analysis_successful": True,
                "overall_score": overall_score,
                "risk_level": risk_level,
                "suspicious_urls": suspicious_urls,
                "suspicious_count": len(suspicious_urls),
                "ai_explanation": ai_response,
                "confidence": "high"
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

@app.post("/analyze")
def analyze_links(data: LinksInput):
    """Analisa uma lista de links usando exclusivamente IA"""
    
    if not data.links:
        return {
            "total_links": 0,
            "suspicious_links": [],
            "risk_level": "low",
            "overall_risk_score": 0,
            "method": "ai_only",
            "message": "Nenhum link para analisar"
        }
    
    # Análise com IA
    ai_result = analyze_links_with_ai(data.links)
    
    # Prepara lista de links suspeitos com detalhes
    suspicious_links = []
    for url in ai_result["suspicious_urls"]:
        suspicious_links.append({
            "url": url,
            "risk_score": ai_result["overall_score"],
            "detection_method": "ai",
            "reason": "Identificado como suspeito pela IA"
        })
    
    # Determina recomendação baseada no score
    score = ai_result["overall_score"]
    if score >= 80:
        recommendation = "BLOQUEAR IMEDIATAMENTE - Risco crítico"
    elif score >= 60:
        recommendation = "BLOQUEAR - Alto risco detectado"
    elif score >= 30:
        recommendation = "REVISAR - Risco médio detectado"
    else:
        recommendation = "PERMITIR - Baixo risco"
    
    return {
        "total_links": len(data.links),
        "analyzed_links": data.links,
        "suspicious_links": suspicious_links,
        "suspicious_count": ai_result["suspicious_count"],
        "risk_level": ai_result["risk_level"],
        "overall_risk_score": ai_result["overall_score"],
        "recommendation": recommendation,
        "confidence": ai_result["confidence"],
        "method": "ai_only",
        "ai_analysis": {
            "explanation": ai_result["ai_explanation"],
            "analysis_successful": ai_result["analysis_successful"]
        }
    }

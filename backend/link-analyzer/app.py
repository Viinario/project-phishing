from fastapi import FastAPI
from pydantic import BaseModel
import re
import requests
from urllib.parse import urlparse
from typing import List
import socket

app = FastAPI()

class LinksInput(BaseModel):
    links: List[str]

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "link-analyzer"}

def analyze_url_structure(url: str) -> dict:
    """Analisa a estrutura da URL em busca de indicadores suspeitos"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        suspicious_indicators = []
        risk_score = 0
        
        # Verifica domínios suspeitos
        suspicious_domains = [
            'bit.ly', 'tinyurl.com', 'goo.gl', 't.co',
            'ow.ly', 'is.gd', 'buff.ly'
        ]
        
        if any(susp_domain in domain for susp_domain in suspicious_domains):
            suspicious_indicators.append("URL encurtada")
            risk_score += 30
        
        # Verifica caracteres suspeitos no domínio
        if re.search(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', domain):
            suspicious_indicators.append("IP ao invés de domínio")
            risk_score += 50
        
        # Verifica homógrafos e typosquatting
        known_domains = ['google', 'microsoft', 'apple', 'amazon', 'facebook', 'instagram']
        for known in known_domains:
            if known in domain and domain != f"{known}.com":
                # Verifica se é uma variação suspeita
                if (len(domain.replace(known, '')) > 4 or 
                    any(char in domain for char in ['goog1e', 'micr0soft', 'app1e'])):
                    suspicious_indicators.append(f"Possível imitação de {known}")
                    risk_score += 40
        
        # Verifica subdomínios excessivos
        subdomain_count = domain.count('.')
        if subdomain_count > 3:
            suspicious_indicators.append("Muitos subdomínios")
            risk_score += 20
        
        # Verifica HTTPS
        if parsed.scheme != 'https':
            suspicious_indicators.append("Não usa HTTPS")
            risk_score += 25
        
        return {
            "url": url,
            "domain": domain,
            "risk_score": min(risk_score, 100),
            "suspicious_indicators": suspicious_indicators,
            "is_suspicious": risk_score >= 40
        }
        
    except Exception as e:
        return {
            "url": url,
            "domain": "unknown",
            "risk_score": 100,
            "suspicious_indicators": ["Erro ao analisar URL"],
            "is_suspicious": True
        }

@app.post("/analyze")
def analyze_links(data: LinksInput):
    """Analisa uma lista de links em busca de indicadores de phishing"""
    
    if not data.links:
        return {
            "total_links": 0,
            "suspicious_links": [],
            "risk_level": "low",
            "overall_risk_score": 0
        }
    
    analyzed_links = []
    suspicious_links = []
    total_risk_score = 0
    
    for link in data.links:
        analysis = analyze_url_structure(link)
        analyzed_links.append(analysis)
        total_risk_score += analysis["risk_score"]
        
        if analysis["is_suspicious"]:
            suspicious_links.append({
                "url": link,
                "risk_score": analysis["risk_score"],
                "indicators": analysis["suspicious_indicators"]
            })
    
    # Calcula o risco geral
    average_risk = total_risk_score / len(data.links) if data.links else 0
    
    if average_risk >= 60:
        risk_level = "high"
    elif average_risk >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "total_links": len(data.links),
        "analyzed_links": analyzed_links,
        "suspicious_links": suspicious_links,
        "suspicious_count": len(suspicious_links),
        "risk_level": risk_level,
        "overall_risk_score": round(average_risk, 2),
        "recommendation": "Bloquear" if average_risk >= 60 else "Revisar" if average_risk >= 30 else "Seguro"
    }

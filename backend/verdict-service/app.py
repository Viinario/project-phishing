from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import re

app = FastAPI()

class AnalysisResult(BaseModel):
    email_analysis: dict
    link_analysis: dict
    sender: str
    subject: str

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "verdict-service"}

@app.post("/verdict")
def generate_final_verdict(data: AnalysisResult):
    """Gera o veredito final baseado nas análises dos microsserviços"""
    
    # Pontuação base
    total_score = 0
    risk_factors = []
    
    # Análise do conteúdo do email (peso: 50%)
    email_result = data.email_analysis
    if email_result.get('is_phishing', False):
        total_score += 50
        risk_factors.append("Conteúdo identificado como phishing pela IA")
    elif email_result.get('risk_level') == 'high':
        total_score += 40
        risk_factors.append("Alto risco detectado no conteúdo")
    elif email_result.get('risk_level') == 'medium':
        total_score += 20
        risk_factors.append("Risco médio detectado no conteúdo")
    
    # Análise dos links (peso: 30%)
    link_result = data.link_analysis
    link_risk_score = link_result.get('overall_risk_score', 0)
    
    if link_risk_score >= 60:
        total_score += 30
        risk_factors.append("Links altamente suspeitos detectados")
    elif link_risk_score >= 30:
        total_score += 15
        risk_factors.append("Links com risco médio detectados")
    
    if link_result.get('suspicious_count', 0) > 0:
        risk_factors.append(f"{link_result['suspicious_count']} link(s) suspeito(s)")
    
    # Análise do remetente (peso: 20%)
    sender = data.sender.lower()
    sender_score = analyze_sender(sender)
    total_score += sender_score
    
    if sender_score > 0:
        risk_factors.append("Remetente suspeito")
    
    # Análise do assunto (peso adicional)
    subject_score = analyze_subject(data.subject)
    total_score += subject_score
    
    if subject_score > 0:
        risk_factors.append("Assunto com características suspeitas")
    
    # Determina o nível de risco
    if total_score >= 70:
        risk_level = "CRÍTICO"
        recommendation = "BLOQUEAR IMEDIATAMENTE - Alta probabilidade de phishing"
        action = "block"
    elif total_score >= 50:
        risk_level = "ALTO"
        recommendation = "BLOQUEAR - Provável phishing"
        action = "block"
    elif total_score >= 30:
        risk_level = "MÉDIO" 
        recommendation = "REVISAR - Características suspeitas detectadas"
        action = "review"
    else:
        risk_level = "BAIXO"
        recommendation = "PERMITIR - Email parece legítimo"
        action = "allow"
    
    return {
        "phishing_score": min(total_score, 100),
        "risk_level": risk_level,
        "is_phishing": total_score >= 50,
        "confidence": "high" if total_score >= 70 or total_score <= 20 else "medium",
        "recommendation": recommendation,
        "action": action,
        "risk_factors": risk_factors,
        "analysis_details": {
            "email_analysis": email_result,
            "link_analysis": link_result,
            "sender_score": sender_score,
            "subject_score": subject_score
        }
    }

def analyze_sender(sender: str) -> int:
    """Analisa o remetente em busca de indicadores suspeitos"""
    score = 0
    
    # Domínios suspeitos comuns
    suspicious_domains = [
        'tempmail', 'guerrillamail', '10minutemail', 'mailinator',
        'throwaway', 'fake', 'temp', 'disposable'
    ]
    
    if any(domain in sender for domain in suspicious_domains):
        score += 15
    
    # Verifica caracteres suspeitos
    if re.search(r'[0-9]{3,}', sender):
        score += 10  # Muitos números
    
    # Verifica domínios que imitam serviços conhecidos
    fake_domains = [
        'gmai1.com', 'yah00.com', 'hotmai1.com', 'goog1e.com',
        'microsooft.com', 'app1e.com'
    ]
    
    if any(fake in sender for fake in fake_domains):
        score += 20
    
    return score

def analyze_subject(subject: str) -> int:
    """Analisa o assunto em busca de características de phishing"""
    score = 0
    subject_lower = subject.lower()
    
    # Palavras de urgência
    urgent_words = [
        'urgente', 'imediato', 'agora', 'hoje', 'expire', 'vence',
        'bloqueio', 'suspensa', 'cancelar', 'verificar'
    ]
    
    urgent_count = sum(1 for word in urgent_words if word in subject_lower)
    score += urgent_count * 5
    
    # Uso excessivo de maiúsculas
    if len(re.findall(r'[A-Z]', subject)) > len(subject) * 0.5:
        score += 10
    
    # Múltiplos pontos de exclamação
    exclamation_count = subject.count('!')
    if exclamation_count >= 2:
        score += exclamation_count * 3
    
    return min(score, 20)  # Máximo 20 pontos do assunto
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import re
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

class AnalysisResult(BaseModel):
    email_analysis: dict
    link_analysis: dict
    sender: str
    subject: str

def analyze_complete_case_with_ai(analysis_data: AnalysisResult) -> Dict[str, Any]:
    """Usa IA para analisar todos os dados e gerar um veredito holístico"""
    try:
        prompt = f"""
        Você é um especialista em detecção de phishing. Analise TODOS os dados abaixo e forneça um veredito final.
        
        ANÁLISE DO EMAIL:
        {json.dumps(analysis_data.email_analysis, indent=2, ensure_ascii=False)}
        
        ANÁLISE DOS LINKS:
        {json.dumps(analysis_data.link_analysis, indent=2, ensure_ascii=False)}
        
        REMETENTE: {analysis_data.sender}
        ASSUNTO: {analysis_data.subject}
        
        Por favor, analise HOLÍSTICAMENTE todos esses dados e retorne um JSON com:
        
        1. "phishing_score": score de 0-100 (onde 100 = phishing certo)
        2. "risk_level": "CRÍTICO" | "ALTO" | "MÉDIO" | "BAIXO"
        3. "is_phishing": true/false
        4. "confidence": "high" | "medium" | "low"
        5. "recommendation": "Recomendação clara para o usuário"
        6. "action": "block" | "review" | "allow"
        7. "detailed_analysis": {{
            "correlation_analysis": "Como diferentes indicadores se correlacionam",
            "pattern_recognition": "Padrões de phishing identificados",
            "context_evaluation": "Avaliação do contexto geral",
            "final_reasoning": "Justificativa final do veredito"
        }}
        8. "risk_factors": [lista de fatores de risco encontrados]
        9. "confidence_factors": [fatores que aumentam a confiança no veredito]
        
        IMPORTANTE: Considere a CORRELAÇÃO entre diferentes análises. Por exemplo:
        - Se email E links são suspeitos = score muito alto
        - Se só um é suspeito = investigar contradições
        - Se remetente legítimo mas conteúdo suspeito = possível conta comprometida
        
        Responda APENAS com JSON válido, sem explicações adicionais.
        """
        
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        
        return {
            "ai_verdict_successful": True,
            "verdict": result
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar resposta da IA: {e}")
        return {
            "ai_verdict_successful": False,
            "error": "Erro ao processar resposta da IA",
            "fallback_verdict": generate_fallback_verdict(analysis_data)
        }
    except Exception as e:
        logger.error(f"Erro na análise com IA: {e}")
        return {
            "ai_verdict_successful": False,
            "error": str(e),
            "fallback_verdict": generate_fallback_verdict(analysis_data)
        }

def generate_fallback_verdict(data: AnalysisResult) -> Dict[str, Any]:
    """Gera veredito de fallback usando lógica tradicional quando IA falha"""
    total_score = 0
    risk_factors = []
    
    # Análise do email (peso: 50%)
    email_result = data.email_analysis
    if email_result.get('is_phishing', False):
        total_score += 50
        risk_factors.append("Conteúdo identificado como phishing")
    elif email_result.get('risk_level') == 'high':
        total_score += 40
        risk_factors.append("Alto risco detectado no conteúdo")
    
    # Análise dos links (peso: 30%)
    link_result = data.link_analysis
    link_score = link_result.get('overall_risk_score', 0)
    total_score += (link_score * 0.3)
    
    if link_score >= 60:
        risk_factors.append("Links altamente suspeitos")
    
    # Determina o nível de risco
    if total_score >= 70:
        risk_level = "CRÍTICO"
        action = "block"
    elif total_score >= 50:
        risk_level = "ALTO"
        action = "block"
    elif total_score >= 30:
        risk_level = "MÉDIO"
        action = "review"
    else:
        risk_level = "BAIXO"
        action = "allow"
    
    return {
        "phishing_score": min(total_score, 100),
        "risk_level": risk_level,
        "is_phishing": total_score >= 50,
        "confidence": "medium",
        "recommendation": f"Veredito automático: {risk_level}",
        "action": action,
        "risk_factors": risk_factors,
        "method": "fallback_logic"
    }

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "verdict-service", "ai_enabled": GEMINI_API_KEY is not None}

@app.post("/verdict")
def generate_final_verdict(data: AnalysisResult):
    """Gera o veredito final usando IA para análise holística"""
    try:
        # Análise principal com IA
        ai_result = analyze_complete_case_with_ai(data)
        
        if ai_result["ai_verdict_successful"]:
            verdict = ai_result["verdict"]
            verdict["analysis_method"] = "ai_holistic"
            verdict["ai_analysis_successful"] = True
            return verdict
        else:
            # Fallback para lógica tradicional
            fallback_verdict = ai_result["fallback_verdict"]
            fallback_verdict["analysis_method"] = "fallback_logic"
            fallback_verdict["ai_analysis_successful"] = False
            fallback_verdict["ai_error"] = ai_result.get("error", "Erro desconhecido")
            return fallback_verdict
            
    except Exception as e:
        logger.error(f"Erro crítico no verdict service: {e}")
        # Último recurso - veredito de emergência
        return {
            "phishing_score": 50,
            "risk_level": "MÉDIO",
            "is_phishing": False,
            "confidence": "low",
            "recommendation": "REVISAR MANUALMENTE - Erro no sistema de análise",
            "action": "review",
            "risk_factors": ["Sistema de análise indisponível"],
            "analysis_method": "emergency_fallback",
            "ai_analysis_successful": False,
            "error": str(e)
        }


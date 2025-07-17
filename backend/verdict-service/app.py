from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import re
import os
import json
import logging
import requests

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class AnalysisResult(BaseModel):
    email_analysis: dict
    link_analysis: dict
    from_address: str
    subject: str

def analyze_complete_case_with_ai(analysis_data: AnalysisResult) -> Dict[str, Any]:
    """Usa IA para analisar todos os dados e gerar um veredito holístico"""
    
    # Verifica se a API key está configurada
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'cole_sua_chave_api_do_gemini_aqui':
        logger.error("GEMINI_API_KEY não configurada")
        return {
            "ai_verdict_successful": False,
            "error": "GEMINI_API_KEY não configurada",
            "fallback_verdict": generate_fallback_verdict(analysis_data)
        }
    
    try:
        prompt = f"""
        Você é um especialista em detecção de phishing. Analise TODOS os dados abaixo e forneça um veredito final.
        
        ANÁLISE DO EMAIL:
        {json.dumps(analysis_data.email_analysis, indent=2, ensure_ascii=False)}
        
        ANÁLISE DOS LINKS:
        {json.dumps(analysis_data.link_analysis, indent=2, ensure_ascii=False)}
        
        REMETENTE: {analysis_data.from_address}
        ASSUNTO: {analysis_data.subject}
        
        FORMATO DE RESPOSTA OBRIGATÓRIO:
        
        PHISHING_SCORE: [Score de 0-100, onde 100 = phishing certo]
        
        RISK_LEVEL: [CRÍTICO | ALTO | MÉDIO | BAIXO]
        
        IS_PHISHING: [true | false]
        
        CONFIDENCE: [high | medium | low]
        
        RECOMMENDATION: [Recomendação clara para o usuário]
        
        ACTION: [block | review | allow]
        
        CORRELATION_ANALYSIS: [Como diferentes indicadores se correlacionam]
        
        PATTERN_RECOGNITION: [Padrões de phishing identificados]
        
        CONTEXT_EVALUATION: [Avaliação do contexto geral]
        
        FINAL_REASONING: [Justificativa final do veredito]
        
        RISK_FACTORS:
        - [Fator de risco 1]
        - [Fator de risco 2]
        - [Fator de risco 3]
        
        CONFIDENCE_FACTORS:
        - [Fator de confiança 1]
        - [Fator de confiança 2]
        
        IMPORTANTE: Considere a CORRELAÇÃO entre diferentes análises.
        """
        
        # Headers para a API
        headers = {
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
                "maxOutputTokens": 8192,
            }
        }
        
        timeout = 30
        
        logger.info("Gerando veredito com Gemini AI")
        
        response = requests.post(
            'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent',
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code != 200:
            logger.error(f"Erro na API do Gemini: {response.status_code}")
            return {
                "ai_verdict_successful": False,
                "error": f"Erro na API do Gemini: {response.status_code}",
                "fallback_verdict": generate_fallback_verdict(analysis_data)
            }
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
            logger.info(f"Resposta do Gemini recebida: {ai_response[:200]}...")
            
            # Primeiro tenta parsing JSON
            try:
                # Remove blocos de código markdown se existirem
                clean_response = ai_response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]  # Remove ```json
                if clean_response.startswith('```'):
                    clean_response = clean_response[3:]  # Remove ```
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]  # Remove ```
                
                clean_response = clean_response.strip()
                
                result_json = json.loads(clean_response)
                
                # Padronizar campos se necessário
                if "PHISHING_SCORE" in result_json:
                    result_json["phishing_score"] = result_json.pop("PHISHING_SCORE")
                if "RISK_LEVEL" in result_json:
                    result_json["risk_level"] = result_json.pop("RISK_LEVEL")
                if "IS_PHISHING" in result_json:
                    result_json["is_phishing"] = result_json.pop("IS_PHISHING")
                if "CONFIDENCE" in result_json:
                    result_json["confidence"] = result_json.pop("CONFIDENCE").lower()
                if "RECOMMENDATION" in result_json:
                    result_json["recommendation"] = result_json.pop("RECOMMENDATION")
                if "ACTION" in result_json:
                    result_json["action"] = result_json.pop("ACTION").lower()
                
                # Estruturar detailed_analysis se campos existirem
                detailed_analysis = {}
                if "CORRELATION_ANALYSIS" in result_json:
                    detailed_analysis["correlation_analysis"] = result_json.pop("CORRELATION_ANALYSIS")
                if "PATTERN_RECOGNITION" in result_json:
                    detailed_analysis["pattern_recognition"] = result_json.pop("PATTERN_RECOGNITION")
                if "CONTEXT_EVALUATION" in result_json:
                    detailed_analysis["context_evaluation"] = result_json.pop("CONTEXT_EVALUATION")
                if "FINAL_REASONING" in result_json:
                    detailed_analysis["final_reasoning"] = result_json.pop("FINAL_REASONING")
                
                if detailed_analysis:
                    result_json["detailed_analysis"] = detailed_analysis
                
                # Extrair listas de fatores
                if "RISK_FACTORS" in result_json:
                    risk_factors = result_json.pop("RISK_FACTORS")
                    if isinstance(risk_factors, list):
                        result_json["risk_factors"] = risk_factors
                    else:
                        result_json["risk_factors"] = []
                
                if "CONFIDENCE_FACTORS" in result_json:
                    confidence_factors = result_json.pop("CONFIDENCE_FACTORS")
                    if isinstance(confidence_factors, list):
                        result_json["confidence_factors"] = confidence_factors
                    else:
                        result_json["confidence_factors"] = []
                
                return {
                    "ai_verdict_successful": True,
                    "verdict": result_json
                }
            except json.JSONDecodeError:
                # Se JSON falhar, faz parsing manual da resposta estruturada
                logger.info("JSON parsing falhou, usando parsing manual")
                
                # Parsing manual da resposta estruturada
                verdict = {}
                
                # Extrai valores principais
                score_match = re.search(r'PHISHING_SCORE:\s*(\d+)', ai_response)
                verdict["phishing_score"] = int(score_match.group(1)) if score_match else 50
                
                risk_match = re.search(r'RISK_LEVEL:\s*(\w+)', ai_response)
                verdict["risk_level"] = risk_match.group(1).upper() if risk_match else "MÉDIO"
                
                phishing_match = re.search(r'IS_PHISHING:\s*(true|false)', ai_response, re.IGNORECASE)
                verdict["is_phishing"] = phishing_match.group(1).lower() == 'true' if phishing_match else False
                
                confidence_match = re.search(r'CONFIDENCE:\s*(\w+)', ai_response)
                verdict["confidence"] = confidence_match.group(1).lower() if confidence_match else "medium"
                
                recommendation_match = re.search(r'RECOMMENDATION:\s*(.+?)(?=\n\n|\nACTION:|$)', ai_response, re.DOTALL)
                verdict["recommendation"] = recommendation_match.group(1).strip() if recommendation_match else "Revisar manualmente"
                
                action_match = re.search(r'ACTION:\s*(\w+)', ai_response)
                verdict["action"] = action_match.group(1).lower() if action_match else "review"
                
                # Análise detalhada
                correlation_match = re.search(r'CORRELATION_ANALYSIS:\s*(.+?)(?=\n\n|\nPATTERN_RECOGNITION:|$)', ai_response, re.DOTALL)
                pattern_match = re.search(r'PATTERN_RECOGNITION:\s*(.+?)(?=\n\n|\nCONTEXT_EVALUATION:|$)', ai_response, re.DOTALL)
                context_match = re.search(r'CONTEXT_EVALUATION:\s*(.+?)(?=\n\n|\nFINAL_REASONING:|$)', ai_response, re.DOTALL)
                reasoning_match = re.search(r'FINAL_REASONING:\s*(.+?)(?=\n\n|\nRISK_FACTORS:|$)', ai_response, re.DOTALL)
                
                verdict["detailed_analysis"] = {
                    "correlation_analysis": correlation_match.group(1).strip() if correlation_match else "Análise não disponível",
                    "pattern_recognition": pattern_match.group(1).strip() if pattern_match else "Padrões não identificados",
                    "context_evaluation": context_match.group(1).strip() if context_match else "Contexto não avaliado",
                    "final_reasoning": reasoning_match.group(1).strip() if reasoning_match else "Justificativa não disponível"
                }
                
                # Extrai fatores de risco
                risk_factors_section = re.search(r'RISK_FACTORS:\s*(.+?)(?=\n\n|\nCONFIDENCE_FACTORS:|$)', ai_response, re.DOTALL)
                if risk_factors_section:
                    risk_factors = re.findall(r'-\s*(.+)', risk_factors_section.group(1))
                    verdict["risk_factors"] = [factor.strip() for factor in risk_factors]
                else:
                    verdict["risk_factors"] = []
                
                # Extrai fatores de confiança
                confidence_factors_section = re.search(r'CONFIDENCE_FACTORS:\s*(.+?)(?=\n\n|$)', ai_response, re.DOTALL)
                if confidence_factors_section:
                    confidence_factors = re.findall(r'-\s*(.+)', confidence_factors_section.group(1))
                    verdict["confidence_factors"] = [factor.strip() for factor in confidence_factors]
                else:
                    verdict["confidence_factors"] = []
                
                return {
                    "ai_verdict_successful": True,
                    "verdict": verdict,
                    "parsing_method": "manual"
                }
        else:
            logger.error("Resposta inválida da API do Gemini")
            return {
                "ai_verdict_successful": False,
                "error": "Resposta inválida da API do Gemini",
                "fallback_verdict": generate_fallback_verdict(analysis_data)
            }
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout na API do Gemini após {timeout}s")
        return {
            "ai_verdict_successful": False,
            "error": f"Timeout na API do Gemini após {timeout}s",
            "fallback_verdict": generate_fallback_verdict(analysis_data)
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de conexão com API do Gemini: {str(e)}")
        return {
            "ai_verdict_successful": False,
            "error": f"Erro ao conectar com a API do Gemini: {str(e)}",
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
    api_key = os.getenv('GEMINI_API_KEY')
    return {"status": "healthy", "service": "verdict-service", "ai_enabled": api_key is not None and api_key != 'cole_sua_chave_api_do_gemini_aqui'}

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


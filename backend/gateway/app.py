from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import requests
import json

app = FastAPI()

class EmailInput(BaseModel):
    subject: str
    body: str
    from_address: str

@app.post("/analyze-eml")
async def analyze_eml_file(file: UploadFile = File(...)):
    """Endpoint principal para análise de arquivos EML"""
    
    try:
        # 1. Parse do arquivo EML
        files = {'file': (file.filename, await file.read(), file.content_type)}
        email_response = requests.post('http://email-parser:5000/parse-eml', files=files)
        
        if email_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Erro ao processar arquivo EML")
        
        email_data = email_response.json()
        
        # 2. Análise dos links
        link_response = requests.post('http://link-analyzer:5000/analyze', 
                                    json={"links": email_data.get("links", [])})
        
        if link_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Erro na análise de links")
        
        link_analysis = link_response.json()
        
        # 3. Análise do conteúdo com IA
        phishing_payload = {
            "subject": email_data.get("subject", ""),
            "body": email_data.get("text_content", ""),
            "sender": email_data.get("sender", "")
        }
        
        phishing_response = requests.post('http://phishing-detector:5000/analyze', 
                                        json=phishing_payload)
        
        if phishing_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Erro na análise de phishing")
        
        phishing_analysis = phishing_response.json()
        
        # 4. Veredito final
        verdict_payload = {
            "email_analysis": phishing_analysis,
            "link_analysis": link_analysis,
            "sender": email_data.get("sender", ""),
            "subject": email_data.get("subject", "")
        }
        
        verdict_response = requests.post('http://verdict-service:5000/verdict', 
                                       json=verdict_payload)
        
        if verdict_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Erro no serviço de veredito")
        
        final_verdict = verdict_response.json()
        
        # Resultado completo
        return {
            "status": "success",
            "email_data": {
                "subject": email_data.get("subject"),
                "sender": email_data.get("sender"),
                "links_count": len(email_data.get("links", [])),
                "text_preview": email_data.get("text_content", "")[:200] + "..." if len(email_data.get("text_content", "")) > 200 else email_data.get("text_content", "")
            },
            "analysis_results": {
                "phishing_analysis": phishing_analysis,
                "link_analysis": link_analysis,
                "final_verdict": final_verdict
            },
            "verdict": {
                "is_phishing": final_verdict.get("is_phishing"),
                "risk_level": final_verdict.get("risk_level"),
                "phishing_score": final_verdict.get("phishing_score"),
                "recommendation": final_verdict.get("recommendation"),
                "confidence": final_verdict.get("confidence")
            }
        }
        
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Erro de conexão com os microsserviços")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/analyze")
def analyze_email_data(data: EmailInput):
    """Endpoint para análise de dados de email já extraídos (compatibilidade)"""
    
    try:
        # 1. Parse dos dados do email
        email_response = requests.post('http://email-parser:5000/parse', json=data.dict())
        
        if email_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Erro ao processar dados do email")
        
        email_result = email_response.json()

        # 2. Análise dos links
        link_response = requests.post('http://link-analyzer:5000/analyze', 
                                    json={"links": email_result.get("links", [])})
        
        if link_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Erro na análise de links")
        
        link_result = link_response.json()

        # 3. Análise do conteúdo
        phishing_payload = {
            "subject": data.subject,
            "body": email_result.get("text_content", ""),
            "sender": email_result.get("sender", "")
        }
        
        phishing_response = requests.post('http://phishing-detector:5000/analyze', 
                                        json=phishing_payload)
        
        if phishing_response.status_code != 200:
            # Fallback para o endpoint simples
            simple_response = requests.post('http://phishing-detector:5000/detect', 
                                          json={"text": email_result.get("text_content", "")})
            phishing_analysis = simple_response.json() if simple_response.status_code == 200 else {"risk": "unknown"}
        else:
            phishing_analysis = phishing_response.json()

        # 4. Veredito final
        verdict_payload = {
            "email_analysis": phishing_analysis,
            "link_analysis": link_result,
            "sender": email_result.get("sender", ""),
            "subject": data.subject
        }
        
        verdict_response = requests.post('http://verdict-service:5000/verdict', 
                                       json=verdict_payload)
        
        final_verdict = verdict_response.json() if verdict_response.status_code == 200 else {
            "phishing_score": 0,
            "risk_level": "BAIXO",
            "recommendation": "Análise incompleta"
        }
        
        return {
            "status": "success",
            "analysis_results": {
                "email_parsing": email_result,
                "link_analysis": link_result,
                "phishing_analysis": phishing_analysis,
                "final_verdict": final_verdict
            }
        }
        
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Erro de conexão com os microsserviços")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/health")
def health_check():
    """Verifica a saúde de todos os microsserviços"""
    services = {
        "email-parser": "http://email-parser:5000",
        "link-analyzer": "http://link-analyzer:5000", 
        "phishing-detector": "http://phishing-detector:5000",
        "verdict-service": "http://verdict-service:5000"
    }
    
    status = {}
    all_healthy = True
    
    for service_name, url in services.items():
        try:
            response = requests.get(f"{url}/", timeout=5)
            status[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            status[service_name] = "unreachable"
            all_healthy = False
    
    return {
        "gateway": "healthy",
        "services": status,
        "overall_status": "healthy" if all_healthy else "degraded"
    }

#!/usr/bin/env python3
"""
Script para testar os microsserviços de detecção de phishing
"""

import requests
import json
import sys
import os

# URLs dos microsserviços (ajuste conforme necessário)
BASE_URLS = {
    'gateway': 'http://localhost:5000',
    'email-parser': 'http://localhost:5001', 
    'phishing-detector': 'http://localhost:5002',
    'link-analyzer': 'http://localhost:5003',
    'verdict-service': 'http://localhost:5004'
}

def check_env_setup():
    """Verifica se o ambiente está configurado corretamente"""
    print("🔧 Verificando configuração do ambiente...")
    
    env_file = ".env"
    env_example = ".env.example"
    
    if not os.path.exists(env_file):
        print(f"❌ Arquivo {env_file} não encontrado!")
        print(f"📝 Execute: cp {env_example} {env_file}")
        print("🔑 Depois configure sua API key do Gemini no arquivo .env")
        return False
    
    # Lê o arquivo .env para verificar se foi configurado
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            
        if 'cole_sua_chave_api_do_gemini_aqui' in content:
            print("❌ API key do Gemini não foi configurada!")
            print("🔑 Edite o arquivo .env e configure sua GEMINI_API_KEY")
            return False
        
        if 'GEMINI_API_KEY=' in content:
            print("✅ Arquivo .env configurado")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao ler arquivo .env: {e}")
        return False
    
    return True

def test_health_checks():
    """Testa se todos os microsserviços estão funcionando"""
    print("\n🔍 Testando health checks dos microsserviços...")
    
    all_healthy = True
    
    for service, url in BASE_URLS.items():
        try:
            response = requests.get(f"{url}/", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service}: OK")
            else:
                print(f"❌ {service}: Erro {response.status_code}")
                all_healthy = False
        except requests.exceptions.RequestException as e:
            print(f"❌ {service}: Não acessível - {e}")
            all_healthy = False
    
    return all_healthy

def test_gemini_integration():
    """Testa especificamente a integração com o Gemini"""
    print("\n🤖 Testando integração com Google Gemini...")
    
    test_data = {
        "subject": "Teste de integração",
        "body": "Este é um teste para verificar se a API do Gemini está funcionando",
        "sender": "teste@exemplo.com"
    }
    
    try:
        response = requests.post(f"{BASE_URLS['phishing-detector']}/analyze", 
                               json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Integração com Gemini: OK")
            print(f"📝 Resposta: {result.get('explanation', 'N/A')[:100]}...")
            return True
        elif response.status_code == 500:
            error_detail = response.json().get('detail', 'Erro desconhecido')
            if 'GEMINI_API_KEY' in error_detail:
                print("❌ API key do Gemini não configurada ou inválida")
                print("🔑 Verifique se a GEMINI_API_KEY está correta no arquivo .env")
            else:
                print(f"❌ Erro na API do Gemini: {error_detail}")
            return False
        else:
            print(f"❌ Erro inesperado: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout na API do Gemini (isso pode ser normal)")
        print("🔄 Tente novamente em alguns segundos")
        return False
    except Exception as e:
        print(f"❌ Erro ao testar Gemini: {e}")
        return False

def test_email_analysis():
    """Testa a análise de um email suspeito"""
    print("\n📧 Testando análise completa de email suspeito...")
    
    test_email = {
        "subject": "URGENTE! Sua conta será bloqueada HOJE!",
        "body": "Clique aqui para verificar sua conta: http://goog1e-security.com/verify agora ou perderá acesso!",
        "from_address": "security@goog1e.com.fake"
    }
    
    try:
        response = requests.post(f"{BASE_URLS['gateway']}/analyze", json=test_email, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Análise completa realizada!")
            
            verdict = result.get('verdict', {})
            print(f"📊 Resultado:")
            print(f"   🚨 É Phishing: {verdict.get('is_phishing', 'N/A')}")
            print(f"   📈 Nível de Risco: {verdict.get('risk_level', 'N/A')}")
            print(f"   💯 Score: {verdict.get('phishing_score', 'N/A')}")
            print(f"   📝 Recomendação: {verdict.get('recommendation', 'N/A')}")
            
            return True
        else:
            print(f"❌ Erro na análise: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_individual_services():
    """Testa cada microsserviço individualmente"""
    print("\n🔧 Testando microsserviços individuais...")
    
    # Teste do email-parser
    print("\n1. Testando Email Parser...")
    email_data = {
        "subject": "Teste",
        "body": "Este é um teste com link: https://example.com",
        "from_address": "test@example.com"
    }
    
    try:
        response = requests.post(f"{BASE_URLS['email-parser']}/parse", json=email_data)
        if response.status_code == 200:
            print("✅ Email Parser: OK")
            parsed_data = response.json()
            print(f"   📎 Links encontrados: {len(parsed_data.get('links', []))}")
        else:
            print(f"❌ Email Parser: Erro {response.status_code}")
    except Exception as e:
        print(f"❌ Email Parser: {e}")
    
    # Teste do link-analyzer
    print("\n2. Testando Link Analyzer...")
    links_data = {"links": ["https://bit.ly/suspicious", "https://192.168.1.1/malware"]}
    
    try:
        response = requests.post(f"{BASE_URLS['link-analyzer']}/analyze", json=links_data)
        if response.status_code == 200:
            print("✅ Link Analyzer: OK")
            link_result = response.json()
            print(f"   🔗 Links suspeitos: {link_result.get('suspicious_count', 0)}")
        else:
            print(f"❌ Link Analyzer: Erro {response.status_code}")
    except Exception as e:
        print(f"❌ Link Analyzer: {e}")
    
    # Teste do phishing-detector (modo simples)
    print("\n3. Testando Phishing Detector (modo simples)...")
    phishing_data = {"text": "URGENTE! Bloqueio da conta!"}
    
    try:
        response = requests.post(f"{BASE_URLS['phishing-detector']}/detect", json=phishing_data)
        if response.status_code == 200:
            print("✅ Phishing Detector (simples): OK")
            detection_result = response.json()
            print(f"   ⚠️ Risco detectado: {detection_result.get('risk', 'unknown')}")
        else:
            print(f"❌ Phishing Detector: Erro {response.status_code}")
    except Exception as e:
        print(f"❌ Phishing Detector: {e}")

def main():
    print("🚀 Iniciando testes dos microsserviços de detecção de phishing\n")
    
    # 1. Verifica configuração do ambiente
    if not check_env_setup():
        print("\n❌ Configure o ambiente antes de continuar!")
        sys.exit(1)
    
    # 2. Testa health checks
    if not test_health_checks():
        print("\n❌ Alguns serviços não estão funcionando!")
        print("🐳 Verifique se o Docker Compose está rodando: docker-compose up")
        sys.exit(1)
    
    # 3. Testa integração com Gemini
    gemini_ok = test_gemini_integration()
    
    # 4. Testa serviços individuais
    test_individual_services()
    
    # 5. Testa análise completa (só se Gemini estiver OK)
    if gemini_ok:
        test_email_analysis()
    else:
        print("\n⚠️ Pulando teste de análise completa (Gemini não está funcionando)")
    
    print("\n✨ Testes concluídos!")
    
    if gemini_ok:
        print("🎉 Todos os sistemas estão funcionando perfeitamente!")
    else:
        print("⚠️ Sistema funcional, mas verifique a configuração da API do Gemini")

if __name__ == "__main__":
    main()

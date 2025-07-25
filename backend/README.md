# Sistema de Detecção de Phishing - Backend

Este projeto implementa um sistema de microsserviços para detecção de phishing em emails usando análise de conteúdo com IA (Google Gemini) e análise de links suspeitos.

## 🏗️ Arquitetura

O sistema é composto por 5 microsserviços:

1. **Gateway** (Porta 5000) - Orquestra todos os outros serviços
2. **Email Parser** (Porta 5001) - Extrai conteúdo de arquivos EML
3. **Phishing Detector** (Porta 5002) - Analisa conteúdo usando IA
4. **Link Analyzer** (Porta 5003) - Analisa URLs suspeitas
5. **Verdict Service** (Porta 5004) - Gera veredito final

## 🚀 Como Executar

### Pré-requisitos

1. Docker e Docker Compose instalados
2. API Key do Google Gemini ([obtenha aqui](https://aistudio.google.com/app/apikey))

### Configuração

1. **Configure a API Key do Gemini:**
   ```bash
   # Copie o arquivo de exemplo
   cp .env.example .env
   
   # Edite o arquivo .env e adicione sua API key
   # IMPORTANTE: NUNCA commite o arquivo .env!
   GEMINI_API_KEY=sua_chave_real_aqui
   ```

2. **Execute os microsserviços:**
   ```bash
   # No diretório backend/
   docker-compose up --build
   ```

3. **Teste a instalação:**
   ```bash
   # Execute o script de teste (verifica configuração e funcionalidade)
   python test_services.py
   ```

## 📋 Endpoints Principais

### Gateway (http://localhost:5000)

#### `POST /analyze-eml`
Analisa um arquivo EML completo.

**Uso:**
```bash
curl -X POST "http://localhost:5000/analyze-eml" \
  -F "file=@exemplo.eml"
```

#### `POST /analyze`
Analisa dados de email já extraídos.

**Payload:**
```json
{
  "subject": "Assunto do email",
  "body": "Corpo do email com possíveis links",
  "from_address": "remetente@exemplo.com"
}
```

**Exemplo:**
```bash
curl -X POST "http://localhost:5000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "URGENTE! Verificar conta",
    "body": "Clique aqui: http://goog1e-security.com/verify",
    "from_address": "security@goog1e.com"
  }'
```

#### `GET /health`
Verifica o status de todos os microsserviços.

### Resposta Típica

```json
{
  "status": "success",
  "email_data": {
    "subject": "URGENTE! Verificar conta",
    "sender": "security@goog1e.com",
    "links_count": 1,
    "text_preview": "Clique aqui:  ou perderá acesso!"
  },
  "verdict": {
    "is_phishing": true,
    "risk_level": "ALTO",
    "phishing_score": 85,
    "recommendation": "BLOQUEAR - Provável phishing",
    "confidence": "high"
  }
}
```

## 🔧 Microsserviços Individuais

### Email Parser (Porta 5001)
- `POST /parse-eml` - Processa arquivo EML
- `POST /parse` - Processa dados de email

### Phishing Detector (Porta 5002)
- `POST /analyze` - Análise com Google Gemini
- `POST /detect` - Análise simples por palavras-chave

### Link Analyzer (Porta 5003)
- `POST /analyze` - Análise de URLs usando exclusivamente IA

### Verdict Service (Porta 5004)
- `POST /verdict` - Gera veredito final combinado

## 🧪 Testando o Sistema

### Teste Rápido com curl

```bash
# Teste de health check
curl http://localhost:5000/health

# Teste com email suspeito
curl -X POST "http://localhost:5000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "BLOQUEIO URGENTE! Sua conta será suspensa!",
    "body": "Clique imediatamente: http://goog1e-verify.com/urgent para evitar bloqueio!",
    "from_address": "security@goog1e-fake.com"
  }'
```

### Script de Teste Automatizado

```bash
# Teste geral do sistema
python test_services.py

# Teste específico do Link Analyzer com IA
python test_link_comparison.py
```

## 🛡️ Funcionalidades de Detecção

### Análise de Conteúdo (IA)
- Usa Google Gemini para análise semântica
- Detecta linguagem de urgência e ameaças
- Identifica táticas comuns de phishing

### Análise de Links (100% IA)
- **Análise Exclusiva com IA**: Usa Google Gemini para detectar todos os tipos de links suspeitos
- **Detecção Contextual**: Identifica padrões complexos que regras tradicionais não capturam
- **Análise Semântica**: Entende o contexto e intenção por trás dos domínios
- **Adaptação Contínua**: Beneficia-se do conhecimento atualizado do modelo de IA

### Análise de Remetente
- Detecta domínios temporários
- Identifica imitações de serviços conhecidos
- Verifica padrões suspeitos

### Análise de Assunto
- Detecta palavras de urgência
- Verifica uso excessivo de maiúsculas
- Conta pontos de exclamação excessivos

## 📊 Sistema de Pontuação

O sistema atribui pontos baseado em:
- **Análise de IA**: até 50 pontos
- **Análise de links**: até 30 pontos  
- **Remetente suspeito**: até 20 pontos
- **Assunto suspeito**: até 20 pontos

### Níveis de Risco:
- **0-29**: BAIXO - Permitir
- **30-49**: MÉDIO - Revisar
- **50-69**: ALTO - Bloquear
- **70-100**: CRÍTICO - Bloquear imediatamente

## 🔧 Configuração Avançada

### Variáveis de Ambiente

```bash
# Obrigatória
GEMINI_API_KEY=sua_chave_aqui

# Opcionais
DEBUG=False
LOG_LEVEL=INFO
```

### Desenvolvimento

Para desenvolvimento local sem Docker:

```bash
# Instalar dependências em cada microsserviço
cd email-parser && pip install -r requirements.txt
cd ../link-analyzer && pip install -r requirements.txt
# ... etc

# Executar cada serviço em terminais separados
cd email-parser && uvicorn app:app --port 5001
cd link-analyzer && uvicorn app:app --port 5003
# ... etc
```

## 🚨 Monitoramento

### Logs
Os logs de cada microsserviço ficam disponíveis via Docker:

```bash
# Ver logs do gateway
docker-compose logs gateway

# Ver logs de todos os serviços
docker-compose logs -f
```

### Health Checks
Todos os serviços expõem endpoints de health check na raiz (`/`).

## 🤝 Contribuindo

1. Faça fork do projeto
2. Crie uma branch para sua feature
3. Adicione testes para novas funcionalidades
4. Execute os testes existentes
5. Submeta um pull request

## 📝 Próximos Passos

- [ ] Implementar cache para resultados da API Gemini
- [ ] Adicionar análise de anexos
- [ ] Implementar whitelist/blacklist de domínios
- [ ] Adicionar métricas e monitoramento
- [ ] Implementar rate limiting
- [ ] Adicionar autenticação entre serviços

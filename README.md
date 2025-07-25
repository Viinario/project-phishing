# Phishing Detector - Docker Setup Completo

## 📁 Estrutura do Projeto

Agora todos os serviços estão dockerizados e podem ser executados com um único comando:

- **Website** (Frontend): HTML/CSS/JavaScript servido via nginx
- **Gateway** (API Principal): Coordena todos os outros serviços  
- **Email Parser**: Processa arquivos .eml
- **Phishing Detector**: Analisa conteúdo de phishing
- **Link Analyzer**: Analisa links suspeitos
- **Verdict Service**: Gera veredito final

## 🚀 Como Usar

### 1. Subir todos os serviços

```bash
cd backend
docker-compose up --build
```

### 2. Acessar os serviços

- 🌐 **Website**: http://phishing-detector.localhost
- 🔗 **API Gateway**: http://localhost:5000
- 📧 **Email Parser**: http://localhost:5001
- 🛡️ **Phishing Detector**: http://localhost:5002
- 🔍 **Link Analyzer**: http://localhost:5003
- ⚖️ **Verdict Service**: http://localhost:5004

### 3. Parar os serviços

```bash
docker-compose down
```

### 4. Rebuild apenas um serviço específico

```bash
# Exemplo: rebuild só o website
docker-compose build website

# Ou rebuild e restart um serviço específico
docker-compose up --build website
```

## 🔧 Configurações

### Website
- **Servidor**: nginx alpine
- **Porta**: 8080
- **Arquivos**: Servidos estaticamente

### Backend Services
- **Linguagem**: Python/Flask
- **Rede**: phishing-net (bridge)
- **Volumes**: Hot reload para desenvolvimento

## 🌐 Como Funciona

1. O usuário acessa o website em http://phishing-detector.localhost
2. Faz upload de um arquivo .eml através da interface
3. O JavaScript envia o arquivo para a API Gateway (localhost:5000)
4. O Gateway coordena a análise com todos os microserviços
5. O resultado é exibido na página de resposta

## 🔄 Desenvolvimento

Para desenvolver o website, você pode:
- Usar o Docker (recomendado para teste completo)
- Ou abrir diretamente no navegador para desenvolvimento de frontend

O JavaScript detecta automaticamente o ambiente e ajusta as URLs da API.

## 📝 Notas Importantes

- Certifique-se de ter o Docker e Docker Compose instalados
- A primeira execução pode demorar mais devido ao download das imagens
- Os logs de todos os serviços aparecerão no terminal
- Use Ctrl+C para parar todos os serviços

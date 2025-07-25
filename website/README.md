# Website Docker Setup

O website agora está configurado para rodar em Docker junto com os demais serviços.

## Como usar

### Subir todos os serviços (incluindo website)

```bash
cd backend
docker-compose up --build
```

### Acessar os serviços

- **Website**: http://phishing-detector.localhost
  - **Página inicial**: http://phishing-detector.localhost/
  - **Página de resultados**: http://phishing-detector.localhost/resposta
- **API Gateway**: http://localhost:5000
- **Email Parser**: http://localhost:5001
- **Phishing Detector**: http://localhost:5002
- **Link Analyzer**: http://localhost:5003
- **Verdict Service**: http://localhost:5004

### Parar os serviços

```bash
docker-compose down
```

## Estrutura

O website utiliza nginx como servidor web para servir os arquivos estáticos HTML, CSS e JavaScript. Está configurado para se comunicar com o backend através da rede Docker interna `phishing-net`.

### URL Routing

O nginx está configurado com rotas personalizadas:
- `/` → serve `index.html` 
- `/resposta` → serve `resposta.html`
- Arquivos estáticos (CSS, JS, imagens) são servidos diretamente

## Desenvolvimento

Para desenvolvimento local, você ainda pode abrir o website diretamente no navegador ou usar um servidor local como Live Server do VS Code. O JavaScript está configurado para detectar automaticamente o ambiente e usar as URLs apropriadas.

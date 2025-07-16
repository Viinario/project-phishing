# 🔐 CONFIGURAÇÃO SEGURA DE API KEYS

## ⚠️ IMPORTANTE - SEGURANÇA DAS CHAVES

Este projeto utiliza a API do Google Gemini que requer uma chave de acesso. Para manter a segurança:

### ✅ O QUE ESTÁ PROTEGIDO

1. **Arquivo `.env` está no `.gitignore`** - Nunca será commitado no Git
2. **Arquivo `.env.example`** - Apenas modelo sem chaves reais
3. **Docker Compose** - Carrega variáveis do arquivo `.env` local

### 🚨 NUNCA FAÇA ISSO

- ❌ Não commite arquivos `.env` no Git
- ❌ Não coloque chaves diretamente no código
- ❌ Não compartilhe suas chaves em mensagens/emails
- ❌ Não use chaves em repositórios públicos

### ✅ CONFIGURAÇÃO CORRETA

1. **Copie o arquivo de exemplo:**
   ```bash
   cp .env.example .env
   ```

2. **Edite o arquivo `.env` com sua chave real:**
   ```bash
   GEMINI_API_KEY=AIzaSyAv8C5iOShDxRo2nX7ah4M7EeZV7favc_I
   ```

3. **Verifique que `.env` está no `.gitignore`:**
   ```bash
   cat .gitignore | grep .env
   # Deve mostrar: .env
   ```

### 🔄 PARA OUTROS DESENVOLVEDORES

Quando alguém clonar o repositório:

1. **Eles verão apenas o `.env.example`**
2. **Precisarão criar seu próprio `.env`**
3. **Devem obter sua própria API key do Google**

### 📝 INSTRUÇÕES PARA NOVOS DESENVOLVEDORES

```bash
# 1. Clone o repositório
git clone <repo-url>
cd project-phishing/backend

# 2. Copie o arquivo de configuração
cp .env.example .env

# 3. Obtenha sua API key do Google Gemini
# Acesse: https://aistudio.google.com/app/apikey
# Faça login e crie uma nova API key

# 4. Edite o arquivo .env com sua chave
# Substitua 'cole_sua_chave_api_do_gemini_aqui' pela sua chave real

# 5. Execute o projeto
docker-compose up --build
```

### 🛡️ VERIFICAÇÃO DE SEGURANÇA

Para verificar se tudo está seguro:

```bash
# Verifica se .env está sendo ignorado pelo Git
git status
# O arquivo .env NÃO deve aparecer na lista

# Verifica se as variáveis estão carregando
docker-compose config
# Deve mostrar as variáveis sem expor os valores
```

### 🚀 PRODUÇÃO

Para deploy em produção, configure as variáveis de ambiente diretamente no servidor:

```bash
# No servidor de produção
export GEMINI_API_KEY=sua_chave_real
docker-compose up -d
```

Ou use serviços de gerenciamento de secrets como:
- AWS Secrets Manager
- Azure Key Vault  
- Google Secret Manager
- HashiCorp Vault

## 🆘 EM CASO DE VAZAMENTO

Se você acidentalmente expor uma API key:

1. **Revogue a chave imediatamente** no Google AI Studio
2. **Gere uma nova chave**
3. **Atualize seu arquivo `.env`**
4. **Force push para remover do histórico** (se necessário):
   ```bash
   git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch .env' --prune-empty --tag-name-filter cat -- --all
   ```

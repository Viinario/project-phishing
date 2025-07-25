/**
 * PÁGINA DE RESULTADO - PHISHING DETECTOR
 *
 * Este arquivo contém toda a lógica para:
 * - Receber dados do arquivo da página anterior
 * - Fazer a análise via API
 * - Exibir os resultados formatados
 * - Gerenciar navegação entre páginas
 */

// ==========================================
// FUNÇÕES DE COMUNICAÇÃO COM API
// ==========================================

/**
 * Função principal para analisar arquivo enviado
 * @param {FormData} formData - Dados do arquivo para análise
 */
async function analyzeFile(formData) {
  try {
    // Fazer requisição para API de análise
    const response = await fetch("http://localhost:5000/analyze-eml", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    // Verificar se a resposta foi bem-sucedida
    if (response.ok) {
      showResult(data);
    } else {
      throw new Error(data.detail || "Erro ao analisar arquivo");
    }
  } catch (error) {
    console.error("Erro na análise:", error);
    showError(error.message);
  }
}

// ==========================================
// FUNÇÕES DE EXIBIÇÃO DE RESULTADOS
// ==========================================

/**
 * Exibe o resultado da análise na tela
 * @param {Object} data - Dados retornados pela API
 */
function showResult(data) {
  const loading = document.getElementById("loading");
  const result = document.getElementById("result");
  const analyzeAnotherBtn = document.getElementById("analyzeAnotherBtn");

  // Esconder indicador de carregamento
  loading.style.display = "none";

  const verdict = data.verdict;

  // Criar HTML com resultado formatado
  result.innerHTML = `
        <div class="result-${verdict.is_phishing ? "danger" : "safe"}">
            <h3>${
              verdict.is_phishing
                ? "⚠️ Possível Phishing Detectado!"
                : "✅ Arquivo Seguro"
            }</h3>
            
            <!-- Informações principais do veredito -->
            <div class="verdict-info">
                <p><strong>Nível de Risco:</strong> ${verdict.risk_level}</p>
                <p><strong>Recomendação:</strong> ${verdict.recommendation}</p>
                ${
                  verdict.phishing_score
                    ? `<p><strong>Score de Phishing:</strong> ${verdict.phishing_score}/100</p>`
                    : ""
                }
                ${
                  verdict.confidence
                    ? `<p><strong>Confiança:</strong> ${verdict.confidence}</p>`
                    : ""
                }
            </div>
            
            <hr style="margin: 15px 0; border: 1px solid #ddd;">
            
            <!-- Detalhes do e-mail analisado -->
            <div class="email-details">
                <h4>📧 Detalhes do E-mail:</h4>
                <p><strong>Remetente:</strong> ${data.email_data.sender}</p>
                <p><strong>Assunto:</strong> ${data.email_data.subject}</p>
                <p><strong>Links encontrados:</strong> ${
                  data.email_data.links_count
                }</p>
            </div>
        </div>
    `;

  // Mostrar resultado e botão para nova análise
  result.style.display = "block";
  analyzeAnotherBtn.style.display = "inline-block";
}

/**
 * Exibe mensagem de erro na tela
 * @param {string} errorMessage - Mensagem de erro a ser exibida
 */
function showError(errorMessage) {
  const loading = document.getElementById("loading");
  const result = document.getElementById("result");
  const analyzeAnotherBtn = document.getElementById("analyzeAnotherBtn");

  // Esconder indicador de carregamento
  loading.style.display = "none";

  // Exibir erro formatado
  result.innerHTML = `
        <div class="result-error">
            <h3>❌ Erro na Análise</h3>
            <p>${errorMessage}</p>
            <p><small>Verifique sua conexão e tente novamente.</small></p>
        </div>
    `;

  result.style.display = "block";
  analyzeAnotherBtn.style.display = "inline-block";
}

// ==========================================
// FUNÇÕES DE NAVEGAÇÃO
// ==========================================

/**
 * Volta para a página inicial
 */
function goBackToHome() {
  window.location.href = "index.html";
}

/**
 * Redireciona para nova análise (limpa dados anteriores)
 */
function analyzeAnother() {
  // Limpar qualquer dado restante no sessionStorage
  sessionStorage.removeItem("fileToAnalyze");
  window.location.href = "index.html";
}

// ==========================================
// FUNÇÕES UTILITÁRIAS
// ==========================================

/**
 * Converte dados base64 de volta para FormData
 * @param {Object} fileData - Objeto com dados do arquivo
 * @returns {FormData} FormData pronto para envio
 */
function createFormDataFromStoredFile(fileData) {
  const formData = new FormData();

  // Decodificar base64 de volta para bytes
  const byteCharacters = atob(fileData.content);
  const byteNumbers = new Array(byteCharacters.length);

  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }

  const byteArray = new Uint8Array(byteNumbers);
  const blob = new Blob([byteArray], { type: "message/rfc822" });

  formData.append("file", blob, fileData.name);
  return formData;
}

// ==========================================
// INICIALIZAÇÃO DA PÁGINA
// ==========================================

/**
 * Função executada quando a página carrega
 */
document.addEventListener("DOMContentLoaded", function () {
  console.log("🚀 Página de resultado carregada");

  // Verificar se há dados do arquivo no sessionStorage
  const fileData = sessionStorage.getItem("fileToAnalyze");

  if (fileData) {
    try {
      // Parsear dados armazenados
      const parsedData = JSON.parse(fileData);
      console.log("📁 Arquivo encontrado:", parsedData.name);

      // Converter para FormData e analisar
      const formData = createFormDataFromStoredFile(parsedData);

      // Limpar dados do sessionStorage
      sessionStorage.removeItem("fileToAnalyze");

      // Iniciar análise
      analyzeFile(formData);
    } catch (error) {
      console.error("❌ Erro ao processar dados do arquivo:", error);
      showError("Erro ao processar dados do arquivo");
    }
  } else {
    // Se não há dados, redirecionar para index
    console.log("⚠️ Nenhum arquivo para análise encontrado, redirecionando...");
    window.location.href = "index.html";
  }
});

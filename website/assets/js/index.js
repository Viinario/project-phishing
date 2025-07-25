/**
 * PÁGINA PRINCIPAL - PHISHING DETECTOR
 *
 * Este arquivo contém toda a lógica para:
 * - Gerenciar upload de arquivos
 * - Validar arquivos EML
 * - Preparar dados para análise
 * - Navegar para página de resultado
 */

// ==========================================
// GERENCIAMENTO DO FORMULÁRIO
// ==========================================

/**
 * Event listener para submissão do formulário
 */
document
  .getElementById("uploadForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();
    console.log("📤 Formulário submetido");

    // Obter elementos da interface
    const fileInput = document.getElementById("fileInput");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const btnText = document.getElementById("btn-text");
    const btnLoading = document.getElementById("btn-loading");
    const uploadText = document.getElementById("upload-text");

    // ==========================================
    // VALIDAÇÕES DO ARQUIVO
    // ==========================================

    // Verificar se arquivo foi selecionado
    if (!fileInput.files[0]) {
      alert("⚠️ Por favor, selecione um arquivo EML.");
      return;
    }

    const file = fileInput.files[0];
    const fileName = file.name;

    console.log("📁 Arquivo selecionado:", fileName);

    // Verificar extensão do arquivo
    if (!fileName.toLowerCase().endsWith(".eml")) {
      alert(
        "❌ Por favor, selecione apenas arquivos .eml (arquivo de e-mail)."
      );
      return;
    }

    // Verificar tamanho do arquivo (limite de 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert("❌ Arquivo muito grande. Limite máximo: 10MB.");
      return;
    }

    // ==========================================
    // PREPARAÇÃO PARA ANÁLISE
    // ==========================================

    // Atualizar interface para estado de carregamento
    setLoadingState(analyzeBtn, btnText, btnLoading, uploadText, true);

    try {
      // Processar arquivo para armazenamento
      await processFileForAnalysis(file);
    } catch (error) {
      console.error("❌ Erro ao processar arquivo:", error);
      alert("Erro ao processar arquivo. Tente novamente.");

      // Restaurar estado da interface
      setLoadingState(analyzeBtn, btnText, btnLoading, uploadText, false);
    }
  });

// ==========================================
// FUNÇÕES DE PROCESSAMENTO DE ARQUIVO
// ==========================================

/**
 * Processa o arquivo para análise posterior
 * @param {File} file - Arquivo selecionado pelo usuário
 */
async function processFileForAnalysis(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = function (e) {
      try {
        // Converter arquivo para base64
        const arrayBuffer = e.target.result;
        const bytes = new Uint8Array(arrayBuffer);
        let binary = "";

        for (let i = 0; i < bytes.byteLength; i++) {
          binary += String.fromCharCode(bytes[i]);
        }

        const base64 = btoa(binary);

        // Armazenar dados no sessionStorage para uso na próxima página
        const fileData = {
          name: file.name,
          content: base64,
          size: file.size,
          timestamp: Date.now(),
        };

        sessionStorage.setItem("fileToAnalyze", JSON.stringify(fileData));
        console.log("💾 Arquivo preparado para análise");

        // Redirecionar para página de resultado
        window.location.href = "/resposta";
        resolve();
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = function () {
      reject(new Error("Erro ao ler arquivo"));
    };

    // Iniciar leitura do arquivo
    reader.readAsArrayBuffer(file);
  });
}

// ==========================================
// FUNÇÕES DE INTERFACE
// ==========================================

/**
 * Controla o estado de carregamento da interface
 * @param {HTMLElement} analyzeBtn - Botão de análise
 * @param {HTMLElement} btnText - Texto do botão
 * @param {HTMLElement} btnLoading - Indicador de carregamento
 * @param {HTMLElement} uploadText - Texto de upload
 * @param {boolean} isLoading - Se está em estado de carregamento
 */
function setLoadingState(
  analyzeBtn,
  btnText,
  btnLoading,
  uploadText,
  isLoading
) {
  if (isLoading) {
    analyzeBtn.disabled = true;
    btnText.style.display = "none";
    btnLoading.style.display = "inline";
    uploadText.textContent = "🔄 Preparando análise...";
  } else {
    analyzeBtn.disabled = false;
    btnText.style.display = "inline";
    btnLoading.style.display = "none";
    uploadText.textContent = "❌ Erro ao processar arquivo. Tente novamente.";
  }
}

/**
 * Trunca nome do arquivo se for muito longo
 * @param {string} fileName - Nome completo do arquivo
 * @returns {string} Nome truncado se necessário
 */
function truncateFileName(fileName) {
  if (fileName.length <= 30) {
    return fileName;
  }

  const extension = fileName.substring(fileName.lastIndexOf("."));
  const nameWithoutExt = fileName.substring(0, fileName.lastIndexOf("."));
  return nameWithoutExt.substring(0, 25) + "..." + extension;
}

// ==========================================
// EVENT LISTENERS
// ==========================================

/**
 * Event listener para mudança de arquivo selecionado
 */
document.getElementById("fileInput").addEventListener("change", function (e) {
  const uploadText = document.getElementById("upload-text");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const fileName = e.target.files[0]?.name;

  if (fileName) {
    console.log("📋 Arquivo selecionado na interface:", fileName);

    // Truncar nome se necessário e atualizar interface
    const displayName = truncateFileName(fileName);
    uploadText.textContent = `📎 Arquivo selecionado: ${displayName}`;

    // Mostrar botão de análise
    analyzeBtn.classList.add("show");
  } else {
    // Resetar interface se nenhum arquivo selecionado
    uploadText.textContent = "📁 Selecione um arquivo EML para análise";
    analyzeBtn.classList.remove("show");
  }
});

// ==========================================
// INICIALIZAÇÃO
// ==========================================

console.log("🚀 Sistema Phishing Detector carregado");
console.log("📋 Aguardando seleção de arquivo...");

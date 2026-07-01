/*
 * assets/js/share.js — Tens Direito
 *
 * Lógica do botão "Partilhar este artigo". Vanilla JS, sem bibliotecas
 * externas, sem frameworks, sem dependências adicionais. Não usa
 * cookies, não contacta nenhum serviço externo, não envia nenhuma
 * informação do utilizador, não introduz nenhum tracker — corre
 * inteiramente no browser do utilizador.
 *
 * Comportamento ao clicar em qualquer elemento ".botao-partilhar":
 *   1. Se existir Web Share API (navigator.share) — usa a partilha
 *      nativa do sistema operativo/browser.
 *   2. Caso contrário (ou se o utilizador cancelar a partilha nativa
 *      não conta como falha) — copia o URL actual para a área de
 *      transferência via navigator.clipboard e mostra uma mensagem
 *      "✅ Ligação copiada para a área de transferência.".
 *   3. Se a cópia automática falhar (ou a API não existir) — mostra
 *      uma caixa simples com o URL num campo de texto, pronta a
 *      seleccionar/copiar manualmente.
 *
 * Usa delegação de eventos em `document` — funciona independentemente
 * de quando o script é carregado (não depende de DOMContentLoaded) e
 * de quantos botões ".botao-partilhar" existirem na página.
 */
(function () {
  "use strict";

  var SELETOR_BOTAO = ".botao-partilhar";
  var MENSAGEM_SUCESSO = "✅ Ligação copiada para a área de transferência.";
  var DURACAO_FEEDBACK_MS = 4000;

  function obterUrlAtual() {
    return window.location.href;
  }

  function obterTitulo() {
    return document.title || "Tens Direito";
  }

  function removerSeExistir(id) {
    var existente = document.getElementById(id);
    if (existente) {
      existente.parentNode.removeChild(existente);
    }
  }

  function mostrarFeedback(mensagem) {
    removerSeExistir("partilhar-feedback");

    var feedback = document.createElement("div");
    feedback.id = "partilhar-feedback";
    feedback.className = "partilhar-feedback";
    feedback.setAttribute("role", "status");
    feedback.setAttribute("aria-live", "polite");
    feedback.textContent = mensagem;
    document.body.appendChild(feedback);

    window.setTimeout(function () {
      removerSeExistir("partilhar-feedback");
    }, DURACAO_FEEDBACK_MS);
  }

  function aoTeclarEscape(evento) {
    if (evento.key === "Escape") {
      fecharCaixaManual();
    }
  }

  function fecharCaixaManual() {
    removerSeExistir("partilhar-manual-overlay");
    document.removeEventListener("keydown", aoTeclarEscape);
  }

  function mostrarCaixaManual(url) {
    fecharCaixaManual();

    var overlay = document.createElement("div");
    overlay.id = "partilhar-manual-overlay";
    overlay.className = "partilhar-manual-overlay";

    var caixa = document.createElement("div");
    caixa.className = "partilhar-manual-caixa";
    caixa.setAttribute("role", "dialog");
    caixa.setAttribute("aria-modal", "true");
    caixa.setAttribute("aria-label", "Copiar ligação manualmente");

    var texto = document.createElement("p");
    texto.textContent = "Não foi possível copiar automaticamente. Copia esta ligação:";
    caixa.appendChild(texto);

    var input = document.createElement("input");
    input.type = "text";
    input.readOnly = true;
    input.value = url;
    input.className = "partilhar-manual-input";
    input.setAttribute("aria-label", "Ligação da página");
    caixa.appendChild(input);

    var fechar = document.createElement("button");
    fechar.type = "button";
    fechar.textContent = "Fechar";
    fechar.className = "partilhar-manual-fechar";
    fechar.setAttribute("aria-label", "Fechar caixa de partilha");
    fechar.addEventListener("click", fecharCaixaManual);
    caixa.appendChild(fechar);

    overlay.appendChild(caixa);
    overlay.addEventListener("click", function (evento) {
      if (evento.target === overlay) {
        fecharCaixaManual();
      }
    });

    document.addEventListener("keydown", aoTeclarEscape);
    document.body.appendChild(overlay);

    input.focus();
    input.select();
  }

  function copiarParaAreaTransferencia(url) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(
        function () {
          mostrarFeedback(MENSAGEM_SUCESSO);
        },
        function () {
          mostrarCaixaManual(url);
        }
      );
    } else {
      mostrarCaixaManual(url);
    }
  }

  function partilhar() {
    var url = obterUrlAtual();
    var titulo = obterTitulo();

    if (navigator.share) {
      navigator.share({ title: titulo, url: url }).catch(function (erro) {
        // Utilizador cancelou a partilha nativa — não é uma falha, não
        // mostrar nenhum fallback.
        if (erro && erro.name === "AbortError") {
          return;
        }
        copiarParaAreaTransferencia(url);
      });
      return;
    }

    copiarParaAreaTransferencia(url);
  }

  document.addEventListener("click", function (evento) {
    var alvo = evento.target;
    var botao = alvo && alvo.closest ? alvo.closest(SELETOR_BOTAO) : null;
    if (!botao) {
      return;
    }
    evento.preventDefault();
    partilhar();
  });
})();

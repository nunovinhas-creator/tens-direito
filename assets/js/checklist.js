/*
 * assets/js/checklist.js — Tens Direito
 *
 * Lógica do bloco ".checklist-final" (FASE 1 de MELHORIAS-SPEC.md):
 * actualiza o contador "X de N concluídos" sempre que uma checkbox muda
 * de estado. Vanilla JS, sem bibliotecas externas.
 *
 * Estado guardado só em memória (no próprio DOM) — nunca em
 * localStorage/sessionStorage/cookies, por desenho: recarregar a página
 * repõe todas as checkboxes por marcar. A spec exige isto explicitamente
 * ("estado em memória, SEM localStorage") para o utilizador nunca julgar
 * que o site "sabe" quem já tratou de quê.
 *
 * Usa delegação de eventos em `document` — funciona independentemente de
 * quando o script é carregado e de quantos blocos ".checklist-final"
 * existirem na página.
 */
(function () {
  "use strict";

  var SELETOR_CAIXA = ".checklist-final";
  var SELETOR_CHECKBOX = 'input[type="checkbox"]';
  var SELETOR_PROGRESSO = ".checklist-progresso";

  function atualizarProgresso(caixa) {
    var progresso = caixa.querySelector(SELETOR_PROGRESSO);
    if (!progresso) {
      return;
    }
    var total = caixa.querySelectorAll(SELETOR_CHECKBOX).length;
    var marcados = caixa.querySelectorAll(SELETOR_CHECKBOX + ":checked").length;
    progresso.textContent = marcados + " de " + total + " concluídos";
  }

  function atualizarTodasAsCaixas() {
    var caixas = document.querySelectorAll(SELETOR_CAIXA);
    for (var i = 0; i < caixas.length; i++) {
      atualizarProgresso(caixas[i]);
    }
  }

  document.addEventListener("change", function (evento) {
    var alvo = evento.target;
    if (!alvo || alvo.type !== "checkbox") {
      return;
    }
    var caixa = alvo.closest ? alvo.closest(SELETOR_CAIXA) : null;
    if (!caixa) {
      return;
    }
    atualizarProgresso(caixa);
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", atualizarTodasAsCaixas);
  } else {
    atualizarTodasAsCaixas();
  }
})();

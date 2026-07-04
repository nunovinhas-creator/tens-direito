/*
 * assets/js/nav.js — Tens Direito
 * Interação da navegação principal injectada por
 * scripts/sincronizar_nav.py (toggle do menu mobile, toggle do
 * dropdown "Apoios", fecho ao clicar fora, Escape e perda de foco).
 * Substitui os scripts inline duplicados (e ligeiramente diferentes)
 * que existiam página a página antes da Fase 4.
 *
 * Escape e fecho ao perder o foco (`focusout`) seguem o padrão
 * "disclosure" do WAI-ARIA Authoring Practices — sem isto, um
 * utilizador de teclado que tabula para fora do menu/dropdown deixava-o
 * aberto visualmente (achado da auditoria WCAG de 2026-07-04).
 */
document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.querySelector('.nav-toggle');
  var menuMovel = document.getElementById('navMobileMenu');
  if (toggle && menuMovel) {
    function fecharMenuMovel() {
      menuMovel.classList.remove('aberto');
      toggle.setAttribute('aria-expanded', 'false');
    }
    toggle.addEventListener('click', function () {
      var aberto = menuMovel.classList.toggle('aberto');
      toggle.setAttribute('aria-expanded', aberto);
    });
    document.addEventListener('click', function (e) {
      if (!menuMovel.contains(e.target) && !toggle.contains(e.target)) {
        fecharMenuMovel();
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && menuMovel.classList.contains('aberto')) {
        fecharMenuMovel();
        toggle.focus();
      }
    });
    menuMovel.addEventListener('focusout', function (e) {
      if (!menuMovel.contains(e.relatedTarget) && e.relatedTarget !== toggle) {
        fecharMenuMovel();
      }
    });
  }

  var dropdown = document.getElementById('navApoiosDropdown');
  var dropdownBtn = dropdown ? dropdown.querySelector('.nav-dropdown-btn') : null;
  if (dropdown && dropdownBtn) {
    function fecharDropdown() {
      dropdown.classList.remove('aberto');
      dropdownBtn.setAttribute('aria-expanded', 'false');
    }
    dropdownBtn.addEventListener('click', function () {
      var aberto = dropdown.classList.toggle('aberto');
      dropdownBtn.setAttribute('aria-expanded', aberto);
    });
    document.addEventListener('click', function (e) {
      if (!dropdown.contains(e.target)) {
        fecharDropdown();
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && dropdown.classList.contains('aberto')) {
        fecharDropdown();
        dropdownBtn.focus();
      }
    });
    dropdown.addEventListener('focusout', function (e) {
      if (!dropdown.contains(e.relatedTarget)) {
        fecharDropdown();
      }
    });
  }

  ['resultados-pesquisa-nav', 'resultados-pesquisa-nav-movel'].forEach(function (idResultados) {
    var idCampo = idResultados.replace('resultados-pesquisa', 'campo-pesquisa');
    document.addEventListener('click', function (e) {
      var div = document.getElementById(idResultados);
      var campo = document.getElementById(idCampo);
      if (div && campo && !div.contains(e.target) && e.target !== campo) {
        div.style.display = 'none';
      }
    });
  });
});

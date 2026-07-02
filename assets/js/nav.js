/*
 * assets/js/nav.js — Tens Direito
 * Interação da navegação principal injectada por
 * scripts/sincronizar_nav.py (toggle do menu mobile, toggle do
 * dropdown "Apoios", fecho ao clicar fora). Substitui os scripts
 * inline duplicados (e ligeiramente diferentes) que existiam página a
 * página antes da Fase 4.
 */
document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.querySelector('.nav-toggle');
  var menuMovel = document.getElementById('navMobileMenu');
  if (toggle && menuMovel) {
    toggle.addEventListener('click', function () {
      var aberto = menuMovel.classList.toggle('aberto');
      toggle.setAttribute('aria-expanded', aberto);
    });
    document.addEventListener('click', function (e) {
      if (!menuMovel.contains(e.target) && !toggle.contains(e.target)) {
        menuMovel.classList.remove('aberto');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  var dropdown = document.getElementById('navApoiosDropdown');
  var dropdownBtn = dropdown ? dropdown.querySelector('.nav-dropdown-btn') : null;
  if (dropdown && dropdownBtn) {
    dropdownBtn.addEventListener('click', function () {
      var aberto = dropdown.classList.toggle('aberto');
      dropdownBtn.setAttribute('aria-expanded', aberto);
    });
    document.addEventListener('click', function (e) {
      if (!dropdown.contains(e.target)) {
        dropdown.classList.remove('aberto');
        dropdownBtn.setAttribute('aria-expanded', 'false');
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

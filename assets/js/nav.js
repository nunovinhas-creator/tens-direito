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
 *
 * Também anima a barra do topo (BARRA-TOPO) — ver iniciarBarraTopo().
 */
document.addEventListener('DOMContentLoaded', function () {
  iniciarBarraTopo();

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

  // Acordeão "Apoios" do menu móvel: abre sozinho quando a página actual
  // pertence a esse grupo (progressive enhancement — sem JS fica fechado,
  // mas o <details> nativo continua a abrir/fechar ao toque). Numa pillar
  // page o pathname coincide com um link do acordeão; num artigo usa-se o
  // link "pertence ao guia" já presente no DOM estático (CLUSTER-BADGE).
  var acordeao = document.getElementById('navMobileApoios');
  if (acordeao) {
    var guiaAtual = document.querySelector('.pertence-guia a');
    var pillarAtual = guiaAtual ? guiaAtual.getAttribute('href') : null;
    acordeao.querySelectorAll('a').forEach(function (link) {
      var href = link.getAttribute('href');
      if (href === location.pathname) {
        link.classList.add('nav-ativo');
        acordeao.open = true;
      } else if (pillarAtual && href === pillarAtual) {
        acordeao.open = true;
      }
    });
  }

  // Medição de conversão: clique nos cartões da grelha de ferramentas do
  // menu móvel e no link "Começa aqui" — evento menu_tool_click, parâmetro
  // tool_destino derivado SEMPRE do href do próprio cartão (basename sem
  // ".html"), nunca um ID fixo por cartão e nunca dados do utilizador.
  // O Measurement ID nunca aparece aqui — o gtag global é inicializado via
  // data-ga4 pelo consentimento.js; guarda typeof gtag como nos restantes
  // eventos (Consent Mode v2 trata do consentimento — zero lógica própria).
  document.querySelectorAll('.nav-mobile-card, .nav-mobile-destaque').forEach(function (cartao) {
    cartao.addEventListener('click', function () {
      if (typeof gtag === 'function') {
        var destino = (cartao.getAttribute('href') || '').split('/').pop().replace(/\.html$/, '');
        gtag('event', 'menu_tool_click', { tool_destino: destino });
      }
    });
  });

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

/*
 * Barra do topo (BARRA-TOPO, injectada por scripts/sincronizar_nav.py):
 * alterna a mensagem do canal de WhatsApp (a única visível sem JS) com a do
 * próximo pagamento da Segurança Social. Progressive enhancement:
 *  - modo estático (gerador de documentos): nada — nem fetch, nem evento,
 *    nem rotação (garantia de rede-zero dessas páginas);
 *  - evento GA4 barra_topo_clique { destino } no clique — só o destino,
 *    nunca dados do utilizador; guarda typeof gtag (Consent Mode v2);
 *  - prefers-reduced-motion, sem tdHojeLisboa, sem dados do mês de Lisboa,
 *    sem pagamento a partir de hoje, ou fetch falhado: fica só a mensagem
 *    do WhatsApp, parada — nunca uma data passada;
 *  - rotação com fade, aria-live="off" (não interrompe leitores de ecrã),
 *    pausa ao hover, ao foco, com a página escondida e no botão de pausa
 *    (WCAG 2.2.2).
 * Datas: #cal-home-dados na homepage (inline, sem pedido) ou
 * data/calendario_barra.json nas outras — ambos escritos por
 * scripts/atualizar_calendario.py, com a mesma função.
 */
function iniciarBarraTopo() {
  var regiao = document.querySelector('.barra-topo-regiao');
  if (!regiao || regiao.getAttribute('data-barra-modo') === 'estatico') return;

  regiao.querySelectorAll('.barra-topo-msg').forEach(function (link) {
    link.addEventListener('click', function () {
      if (typeof gtag === 'function') {
        gtag('event', 'barra_topo_clique', { destino: link.getAttribute('data-destino') });
      }
    });
  });

  var caixa = regiao.querySelector('.barra-topo-mensagens');
  var msgCal = regiao.querySelector('.barra-topo-msg[data-destino="calendario"]');
  var msgWa = regiao.querySelector('.barra-topo-msg[data-destino="whatsapp"]');
  var pausa = regiao.querySelector('.barra-topo-pausa');
  if (!caixa || !msgCal || !msgWa || !pausa) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (typeof window.tdHojeLisboa !== 'function') return;

  function comDados(porMes) {
    var hoje = window.tdHojeLisboa();
    var itens = porMes && porMes[hoje.chave];
    if (!Array.isArray(itens)) return;
    var prox = null;
    for (var i = 0; i < itens.length; i++) {
      var it = itens[i];
      if (it && typeof it.dia === 'number' && typeof it.resumo === 'string' && it.dia >= hoje.dia) {
        prox = it;
        break;
      }
    }
    if (!prox) return;  // pagamentos do mês já feitos — só a mensagem do WhatsApp
    preencherCalendario(prox, hoje.mes);
    animar();
  }

  function preencherCalendario(prox, mes) {
    var nomes = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
    var longo = msgCal.querySelector('.barra-topo-longo');
    var curto = msgCal.querySelector('.barra-topo-curto');
    if (!longo || !curto) return;
    function escrever(alvo, destaque, resto) {
      alvo.textContent = '📅 Próximo pagamento: ';
      var forte = document.createElement('strong');
      forte.textContent = destaque;
      alvo.appendChild(forte);
      if (resto) alvo.appendChild(document.createTextNode(resto));
    }
    escrever(longo, prox.dia + ' de ' + nomes[mes - 1], ' — ' + prox.resumo);
    escrever(curto, 'dia ' + prox.dia, '');
  }

  function animar() {
    var INTERVALO = 6000;
    var FADE = 400;
    var atual = msgWa;
    var timer = null;
    var pausadoPeloUtilizador = false;
    var sobre = false;
    var focado = false;

    function parado() {
      return pausadoPeloUtilizador || sobre || focado || document.hidden;
    }
    function agendar() {
      clearTimeout(timer);
      timer = parado() ? null : setTimeout(trocar, INTERVALO);
    }
    function trocar() {
      timer = null;
      if (parado()) return;
      var seguinte = atual === msgWa ? msgCal : msgWa;
      caixa.classList.add('barra-topo-a-trocar');
      setTimeout(function () {
        atual.hidden = true;
        seguinte.hidden = false;
        atual = seguinte;
        caixa.classList.remove('barra-topo-a-trocar');
        agendar();
      }, FADE);
    }

    regiao.addEventListener('mouseenter', function () { sobre = true; agendar(); });
    regiao.addEventListener('mouseleave', function () { sobre = false; agendar(); });
    regiao.addEventListener('focusin', function () { focado = true; agendar(); });
    regiao.addEventListener('focusout', function (e) {
      if (!regiao.contains(e.relatedTarget)) { focado = false; agendar(); }
    });
    document.addEventListener('visibilitychange', agendar);
    pausa.addEventListener('click', function () {
      pausadoPeloUtilizador = !pausadoPeloUtilizador;
      // "Retomar" é um pedido explícito: retoma já, mesmo com o foco ou o
      // rato ainda na barra (padrão de carrossel do WAI-ARIA APG).
      if (!pausadoPeloUtilizador) { sobre = false; focado = false; }
      pausa.setAttribute('aria-label', pausadoPeloUtilizador ? 'Retomar as mensagens' : 'Pausar as mensagens');
      pausa.setAttribute('data-pausado', pausadoPeloUtilizador ? 'true' : 'false');
      agendar();
    });

    regiao.classList.add('barra-topo-animada');
    pausa.hidden = false;
    agendar();
  }

  var inline = document.getElementById('cal-home-dados');
  if (inline) {
    var porMes = null;
    try { porMes = JSON.parse(inline.textContent); } catch (e) { return; }
    comDados(porMes);
    return;
  }
  var url = regiao.getAttribute('data-barra-dados');
  if (!url || typeof fetch !== 'function') return;
  fetch(url)
    .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(comDados)
    .catch(function () { /* sem datas — fica só a mensagem do WhatsApp */ });
}

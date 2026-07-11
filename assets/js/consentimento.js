/*
 * Tens Direito — banner de consentimento de cookies (próprio, self-hosted).
 *
 * Substitui o CookieYes (2026-07-11): zero serviços externos, zero limites
 * de visualizações, mesma conformidade RGPD por bloqueio real de script —
 * o Google Analytics (gtag.js) NUNCA é carregado antes de o visitante
 * clicar "Aceitar". Rejeitar (ou não responder) mantém a página 100% sem
 * pedidos de rede de analytics.
 *
 * Integração por página (o stub inline no <head> define window.dataLayer,
 * a função global gtag() e o Consent Mode v2 com tudo negado por omissão,
 * antes de qualquer outra coisa):
 *
 *   <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
 *   gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied'});</script>
 *   <script src="/assets/js/consentimento.js" data-ga4="G-XP46PM8H1Q" defer></script>
 *
 * A escolha fica em localStorage (chave "td_consentimento": "aceite" ou
 * "recusado") — é o único armazenamento usado, e é exactamente o propósito
 * dele: lembrar a decisão para o banner não reaparecer a cada página.
 * window.tdGerirConsentimento() reabre o banner (usado em privacidade.html).
 */
(function () {
  'use strict';

  var CHAVE = 'td_consentimento';
  var script = document.currentScript;
  var GA4_ID = (script && script.getAttribute('data-ga4')) || '';

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  if (typeof window.gtag !== 'function') { window.gtag = gtag; }

  function lerEscolha() {
    try { return window.localStorage.getItem(CHAVE); } catch (e) { return null; }
  }

  function guardarEscolha(valor) {
    // Modo privado/armazenamento bloqueado: a escolha vale só para esta
    // página — o banner volta a aparecer na próxima, nunca se assume nada.
    try { window.localStorage.setItem(CHAVE, valor); } catch (e) { /* sem persistência */ }
  }

  var gaCarregado = false;
  function carregarGA() {
    if (gaCarregado || !GA4_ID) { return; }
    gaCarregado = true;
    window.gtag('consent', 'update', { analytics_storage: 'granted' });
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA4_ID;
    document.head.appendChild(s);
    window.gtag('js', new Date());
    window.gtag('config', GA4_ID);
  }

  function apagarCookiesGA() {
    // Best-effort: expira _ga e _ga_* (os únicos cookies que o GA4 cria)
    // no caminho raiz e no domínio-mãe, para quando alguém muda de
    // "aceite" para "recusado" em privacidade.html.
    var partes = document.cookie ? document.cookie.split(';') : [];
    for (var i = 0; i < partes.length; i++) {
      var nome = partes[i].split('=')[0].trim();
      if (nome === '_ga' || nome.indexOf('_ga_') === 0) {
        var exp = '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
        document.cookie = nome + exp;
        document.cookie = nome + exp + '; domain=.' + window.location.hostname;
      }
    }
  }

  var banner = null;

  function fecharBanner() {
    if (banner && banner.parentNode) { banner.parentNode.removeChild(banner); }
    banner = null;
  }

  function aceitar() {
    guardarEscolha('aceite');
    fecharBanner();
    carregarGA();
  }

  function recusar() {
    guardarEscolha('recusado');
    fecharBanner();
    window.gtag('consent', 'update', { analytics_storage: 'denied' });
    apagarCookiesGA();
  }

  function garantirEstilos() {
    if (document.getElementById('td-consent-css')) { return; }
    var css = [
      '.td-consent{position:fixed;left:0;right:0;bottom:0;z-index:9999;background:#0F766E;color:#FFFFFF;',
      'padding:16px 20px;display:flex;flex-wrap:wrap;gap:12px 24px;align-items:center;justify-content:center;',
      'font-size:.95rem;line-height:1.5;box-shadow:0 -2px 12px rgba(0,0,0,.25);}',
      '.td-consent-texto{margin:0;max-width:640px;}',
      '.td-consent-texto a{color:#FFFFFF;text-decoration:underline;text-underline-offset:2px;}',
      '.td-consent-botoes{display:flex;gap:12px;flex-wrap:wrap;}',
      '.td-consent-btn{min-height:44px;min-width:110px;padding:10px 22px;border-radius:8px;',
      'font-size:1rem;font-weight:600;cursor:pointer;font-family:inherit;}',
      '.td-consent-aceitar{background:#FFFFFF;color:#0F766E;border:2px solid #FFFFFF;}',
      '.td-consent-recusar{background:transparent;color:#FFFFFF;border:2px solid #FFFFFF;}',
      '.td-consent-btn:hover{opacity:.92;}',
      '.td-consent-btn:focus-visible{outline:3px solid #FFFFFF;outline-offset:2px;}'
    ].join('');
    var style = document.createElement('style');
    style.id = 'td-consent-css';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function mostrarBanner() {
    if (banner || !document.body) { return; }
    garantirEstilos();

    banner = document.createElement('div');
    banner.className = 'td-consent';
    banner.id = 'td-consent';
    banner.setAttribute('role', 'region');
    banner.setAttribute('aria-label', 'Consentimento de cookies');

    var texto = document.createElement('p');
    texto.className = 'td-consent-texto';
    texto.appendChild(document.createTextNode(
      'Usamos cookies apenas para estatísticas anónimas de visitas (Google Analytics) — e só se aceitares. Sem aceitação, nenhum cookie de análise é colocado. '
    ));
    var link = document.createElement('a');
    link.href = '/privacidade.html';
    link.textContent = 'Política de privacidade';
    texto.appendChild(link);

    var botoes = document.createElement('div');
    botoes.className = 'td-consent-botoes';

    var btnRecusar = document.createElement('button');
    btnRecusar.type = 'button';
    btnRecusar.className = 'td-consent-btn td-consent-recusar';
    btnRecusar.textContent = 'Rejeitar';
    btnRecusar.addEventListener('click', recusar);

    var btnAceitar = document.createElement('button');
    btnAceitar.type = 'button';
    btnAceitar.className = 'td-consent-btn td-consent-aceitar';
    btnAceitar.textContent = 'Aceitar';
    btnAceitar.addEventListener('click', aceitar);

    botoes.appendChild(btnRecusar);
    botoes.appendChild(btnAceitar);
    banner.appendChild(texto);
    banner.appendChild(botoes);
    document.body.appendChild(banner);
  }

  // Reabrir o banner a partir de qualquer página (ex.: privacidade.html).
  window.tdGerirConsentimento = function () {
    fecharBanner();
    mostrarBanner();
  };

  var escolha = lerEscolha();
  if (escolha === 'aceite') {
    carregarGA();
  } else if (escolha !== 'recusado') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', mostrarBanner);
    } else {
      mostrarBanner();
    }
  }
})();

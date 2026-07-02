var paginas = [
  {url: '/abono-de-familia.html',
   titulo: 'Abono de família 2026',
   keywords: 'abono família escalão valor pedir segurança social ias criança jovem'},
  {url: '/p/apoios-escolares.html',
   titulo: 'Apoios Escolares 2026/2027 — guia completo',
   keywords: 'apoios escolares ase bolsa mérito manuais mega passe sub23 candidatura setembro cluster'},
  {url: '/acao-social-escolar.html',
   titulo: 'Ação Social Escolar 2026/2027',
   keywords: 'ase ação social escolar refeições manuais transportes escalão dge'},
  {url: '/bolsa-de-merito.html',
   titulo: 'Bolsa de mérito 2026',
   keywords: 'bolsa mérito secundário valor candidatura escola'},
  {url: '/manuais-escolares-mega.html',
   titulo: 'Manuais escolares gratuitos MEGA',
   keywords: 'manuais escolares gratuitos mega vales levantar voucher dge'},
  {url: '/passe-sub23.html',
   titulo: 'Passe sub-23 gratuito',
   keywords: 'passe sub23 gratuito transportes como pedir metro bus comboio'},
  {url: '/subsidio-parental.html',
   titulo: 'Licença parental 2026 — subsídio parental',
   keywords: 'subsidio parental licenca maternidade paternidade nascimento valor dias modalidades'},
  {url: '/rsi.html',
   titulo: 'RSI 2026 — Rendimento Social de Inserção',
   keywords: 'rsi rendimento social insercao pobreza extrema valor como pedir segurança social'},
  {url: '/subsidio-desemprego.html',
   titulo: 'Subsídio de desemprego 2026',
   keywords: 'subsidio desemprego iefp segurança social como pedir inscricao involuntario'},
  {url: '/complemento-solidario-idosos.html',
   titulo: 'Complemento Solidário para Idosos (CSI) 2026',
   keywords: 'csi complemento solidário idosos apoio reforma pensão idade valor como pedir bas'},
  {url: '/cuidador-informal.html',
   titulo: 'Estatuto do Cuidador Informal 2026',
   keywords: 'cuidador informal estatuto subsídio apoio dependência ias seguro social voluntário majoração'},
  {url: '/amim.html',
   titulo: 'AMIM — Atestado de Incapacidade Multiuso',
   keywords: 'amim atestado multiuso incapacidade junta médica 60% deficiência benefícios fiscais psi'},
  {url: '/prestacao-social-unica.html',
   titulo: 'Prestação Social Única (PSU) 2026',
   keywords: 'psu prestação social única rsi subsídio apoio unificado 13 apoios aprovado parlamento'},
  {url: '/psu-quando-entra-em-vigor.html',
   titulo: 'PSU 2026: o que já foi aprovado e o que ainda falta decidir',
   keywords: 'psu quando entra vigor decreto-lei prazo prr ago 2026 jan 2027 timeline'},
  {url: '/psu-quem-tem-direito.html',
   titulo: 'Quem tem direito à PSU (condições de acesso aprovadas)',
   keywords: 'psu quem tem direito condições acesso residência cidadania rendimento adultos equivalentes trabalho social'},
  {url: '/psu-vs-abono-familia.html',
   titulo: 'PSU e Abono de Família: são apoios diferentes',
   keywords: 'psu abono família diferença subsistema familiar excluído mantém csi'},
  {url: '/psu-lista-13-apoios.html',
   titulo: 'As 13 prestações que a PSU vai substituir (lista completa)',
   keywords: 'psu 13 prestações substituir lista rsi subsídio social desemprego pensão social regime transitório'},
  {url: '/simulador-abono.html',
   titulo: 'Simulador de Abono de Família 2026',
   keywords: 'simulador abono família 2026 escalão rendimento referência calculadora'},
  {url: '/simulador-ase.html',
   titulo: 'Simulador de Ação Social Escolar (ASE) 2026/2027',
   keywords: 'simulador ase ação social escolar escalão rendimento refeições material transportes 2026'},
  {url: '/comecar-aqui.html',
   titulo: 'Começa aqui — encontra o teu apoio',
   keywords: 'comecar começar por onde apoio situação família trabalho estudar desemprego'},
  {url: '/p/familia.html',
   titulo: 'Apoios para Família e Crianças 2026',
   keywords: 'família crianças abono licença parental subsidio parental cluster guia'},
  {url: '/p/idosos-incapacidade-cuidadores.html',
   titulo: 'Apoios para Idosos, Incapacidade e Cuidadores 2026',
   keywords: 'idosos incapacidade cuidadores csi complemento solidário cuidador informal amim cluster guia'},
  {url: '/p/trabalho-rendimento.html',
   titulo: 'Apoios de Trabalho e Rendimento 2026',
   keywords: 'trabalho rendimento desemprego rsi subsidio cluster guia'},
  {url: '/noticias.html',
   titulo: 'Notícias',
   keywords: 'notícias novidades alterações apoios'}
];

function pesquisar(termo) {
  var t = termo.toLowerCase().trim();
  if (!t) return [];
  return paginas.filter(function(p) {
    return p.titulo.toLowerCase().indexOf(t) !== -1 ||
           p.keywords.toLowerCase().indexOf(t) !== -1;
  });
}

function mostrarResultados(resultados, termo) {
  var div = document.getElementById('resultados-pesquisa');
  if (!div) return;
  if (!termo.trim()) {
    div.style.display = 'none';
    div.innerHTML = '';
    return;
  }
  if (!resultados.length) {
    div.innerHTML = '<p style="padding:0.5rem 0.75rem;color:#6c757d;margin:0;">Sem resultados para “' + termo + '”</p>';
  } else {
    div.innerHTML = resultados.map(function(r) {
      return '<a href="' + r.url + '" style="display:block;padding:0.5rem 0.75rem;color:#0F172A;text-decoration:none;border-bottom:1px solid #f0f0f0;" onmouseover="this.style.background=\'#f8f9fa\'" onmouseout="this.style.background=\'\'">' + r.titulo + '</a>';
    }).join('');
  }
  div.style.display = 'block';
}

document.addEventListener('click', function(e) {
  var div = document.getElementById('resultados-pesquisa');
  var input = document.getElementById('campo-pesquisa');
  if (div && input && !div.contains(e.target) && e.target !== input) {
    div.style.display = 'none';
  }
});

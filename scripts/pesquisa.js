var paginas = [
  {url: '/abono-de-familia.html',
   titulo: 'Abono de família 2026',
   keywords: 'abono família escalão valor pedir segurança social ias criança jovem'},
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
  {url: '/subsidio-desemprego.html',
   titulo: 'Subsídio de desemprego 2026',
   keywords: 'subsidio desemprego iefp segurança social como pedir inscricao involuntario'},
  {url: '/comecar-aqui.html',
   titulo: 'Começa aqui — encontra o teu apoio',
   keywords: 'comecar começar por onde apoio situação família trabalho estudar desemprego'},
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

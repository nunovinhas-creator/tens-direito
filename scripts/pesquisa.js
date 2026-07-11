// Índice de pesquisa interna — dados curados aqui (título/descrição/
// keywords precisam de mais nuance do que data/clusters.json guarda),
// mas `cluster`/`clusterNome`/`tipo` têm de bater certo com
// data/clusters.json — verificado por tests/test_pesquisa_indice.py,
// que falha se este ficheiro divergir da fonte única.
var paginas = [
  {url: '/abono-de-familia.html',
   titulo: 'Abono de família 2026',
   descricao: 'Valores do abono de família 2026 por escalão: até 190,98€/mês para bebés, quem tem direito, Garantia Infância, majorações e como pedir.',
   keywords: 'abono família escalão valor pedir segurança social ias criança jovem',
   cluster: 'familia', clusterNome: 'Família e Crianças', tipo: 'artigo'},
  {url: '/p/apoios-escolares.html',
   titulo: 'Apoios Escolares 2026/2027 — guia completo',
   descricao: 'Quatro apoios escolares em Portugal: ASE, bolsa de mérito, manuais MEGA e passe sub-23. O que existe, para quem, quando candidatar e como acumular.',
   keywords: 'apoios escolares ase bolsa mérito manuais mega passe sub23 candidatura setembro cluster',
   cluster: 'apoios-escolares', clusterNome: 'Apoios Escolares', tipo: 'pillar'},
  {url: '/acao-social-escolar.html',
   titulo: 'Ação Social Escolar 2026/2027',
   descricao: 'Guia completo da Ação Social Escolar 2026/2027: escalões A e B, o que cobre, como candidatar no agrupamento e prazos.',
   keywords: 'ase ação social escolar refeições manuais transportes escalão dge',
   cluster: 'apoios-escolares', clusterNome: 'Apoios Escolares', tipo: 'artigo'},
  {url: '/bolsa-de-merito.html',
   titulo: 'Bolsa de mérito 2026',
   descricao: 'Quem tem direito à bolsa de mérito, requisitos de nota e como candidatar em 2026/2027. Candidaturas em setembro.',
   keywords: 'bolsa mérito secundário valor candidatura escola',
   cluster: 'apoios-escolares', clusterNome: 'Apoios Escolares', tipo: 'artigo'},
  {url: '/bolsa-de-estudo-ensino-superior.html',
   titulo: 'Bolsa de Estudo do Ensino Superior 2026/2027',
   descricao: 'Bolsa de ação social para estudantes do ensino superior: condições, candidatura na plataforma BeOn e prazos.',
   keywords: 'bolsa estudo ensino superior dges ies beon universidade politécnico rendimento candidatura',
   cluster: 'apoios-escolares', clusterNome: 'Apoios Escolares', tipo: 'artigo'},
  {url: '/manuais-escolares-mega.html',
   titulo: 'Manuais escolares gratuitos MEGA',
   descricao: 'Manuais escolares gratuitos para todos os alunos do 1.º ao 12.º ano do ensino público. Como registar em manuaisescolares.pt.',
   keywords: 'manuais escolares gratuitos mega vales levantar voucher dge',
   cluster: 'apoios-escolares', clusterNome: 'Apoios Escolares', tipo: 'artigo'},
  {url: '/passe-sub23.html',
   titulo: 'Passe sub-23 gratuito',
   descricao: 'Passe de transportes gratuito para jovens dos 4 aos 23 anos (ou 25 em cursos integrados). Quem tem direito e onde pedir.',
   keywords: 'passe sub23 gratuito transportes como pedir metro bus comboio',
   cluster: 'apoios-escolares', clusterNome: 'Apoios Escolares', tipo: 'artigo'},
  {url: '/prova-escolar.html',
   titulo: 'Prova Escolar 2026: prazo 31 de julho',
   descricao: 'Prova Escolar até 31 de julho: quem tem de fazer (14+, 16+, 18+ com pensão), como verificar se já está registada e o que acontece se falhares o prazo.',
   keywords: 'prova escolar prazo 31 julho abono suspenso segurança social direta bolsa estudo pensão sobrevivência',
   cluster: 'apoios-escolares', clusterNome: 'Apoios Escolares', tipo: 'artigo'},
  {url: '/subsidio-parental.html',
   titulo: 'Licença parental 2026 — subsídio parental',
   descricao: 'Subsídio parental 2026: modalidades de 120 a 180 dias, percentagens do salário, cálculo da remuneração de referência, como pedir em gov.pt.',
   keywords: 'subsidio parental licenca maternidade paternidade nascimento valor dias modalidades',
   cluster: 'familia', clusterNome: 'Família e Crianças', tipo: 'artigo'},
  {url: '/assistencia-familia-filhos.html',
   titulo: 'Faltas para assistência a filhos e família 2026',
   descricao: 'Até 30 dias por ano para faltar por um filho doente, com subsídio da Segurança Social. Regras 2026: quantos dias, valores e como pedir.',
   keywords: 'faltas assistencia filho doente familia subsidio dias cuidar avos neto deficiencia doenca cronica oncologica rp5052',
   cluster: 'familia', clusterNome: 'Família e Crianças', tipo: 'artigo'},
  {url: '/rsi.html',
   titulo: 'RSI 2026 — Rendimento Social de Inserção',
   descricao: 'RSI 2026: valores, condições e como pedir. O RSI será absorvido pela Prestação Social Única (PSU), aprovada em junho 2026.',
   keywords: 'rsi rendimento social insercao pobreza extrema valor como pedir segurança social',
   cluster: 'trabalho-rendimento', clusterNome: 'Trabalho e Rendimento', tipo: 'artigo'},
  {url: '/subsidio-desemprego.html',
   titulo: 'Subsídio de desemprego 2026',
   descricao: 'Descobre se tens direito, quanto vais receber (65% do salário, mín. 537,13€), quanto tempo dura e como pedir em 90 dias.',
   keywords: 'subsidio desemprego iefp segurança social como pedir inscricao involuntario duracao quanto tempo parcial part-time irs',
   cluster: 'trabalho-rendimento', clusterNome: 'Trabalho e Rendimento', tipo: 'artigo'},
  {url: '/baixa-medica-subsidio-doenca.html',
   titulo: 'Baixa médica e subsídio de doença 2026',
   descricao: 'Baixa médica 2026: percentagens do subsídio (55% a 75%), dias de espera, autodeclaração de doença no SNS24, prazos do CIT e fiscalização.',
   keywords: 'baixa médica subsídio doença autodeclaração autobaixa cit certificado incapacidade temporária sns24 junta médica',
   cluster: 'trabalho-rendimento', clusterNome: 'Trabalho e Rendimento', tipo: 'artigo'},
  {url: '/complemento-solidario-idosos.html',
   titulo: 'Complemento Solidário para Idosos (CSI) 2026',
   descricao: 'CSI 2026: idosos com rendimentos abaixo de 8.040€/ano podem receber até 670€/mês. Desde 2024, os rendimentos dos filhos deixaram de contar.',
   keywords: 'csi complemento solidário idosos apoio reforma pensão idade valor como pedir bas',
   cluster: 'idosos-incapacidade-cuidadores', clusterNome: 'Idosos, Incapacidade e Cuidadores', tipo: 'artigo'},
  {url: '/cuidador-informal.html',
   titulo: 'Estatuto do Cuidador Informal 2026',
   descricao: 'Estatuto do Cuidador Informal 2026: subsídio até 590,84 €/mês (1,1 × IAS), condições de elegibilidade e como pedir.',
   keywords: 'cuidador informal estatuto subsídio apoio dependência ias seguro social voluntário majoração',
   cluster: 'idosos-incapacidade-cuidadores', clusterNome: 'Idosos, Incapacidade e Cuidadores', tipo: 'artigo'},
  {url: '/amim.html',
   titulo: 'AMIM — Atestado de Incapacidade Multiuso',
   descricao: 'Guia completo e verificado sobre o AMIM em Portugal: quem pode pedir, junta médica, percentagens, o limiar dos 60%, benefícios fiscais.',
   keywords: 'amim atestado multiuso incapacidade junta médica 60% deficiência benefícios fiscais psi',
   cluster: 'idosos-incapacidade-cuidadores', clusterNome: 'Idosos, Incapacidade e Cuidadores', tipo: 'artigo'},
  {url: '/prestacao-social-para-a-inclusao.html',
   titulo: 'Prestação Social para a Inclusão (PSI) 2026',
   descricao: 'PSI 2026: componente base 333,64€/mês, complemento até 670€/mês, quem tem direito (AMIM ≥60%), acumulação e como pedir na Segurança Social Direta.',
   keywords: 'psi prestação social inclusão deficiência amim 60% componente base complemento majoração valor como pedir',
   cluster: 'idosos-incapacidade-cuidadores', clusterNome: 'Idosos, Incapacidade e Cuidadores', tipo: 'artigo'},
  {url: '/prestacao-social-unica.html',
   titulo: 'Prestação Social Única (PSU) 2026',
   descricao: 'PSU 2026: aprovada em Parlamento 25/06/2026, unifica 13 apoios em regime único não contributivo. Ainda não em vigor — aguarda decreto-lei.',
   keywords: 'psu prestação social única rsi subsídio apoio unificado 13 apoios aprovado parlamento',
   cluster: 'prestacao-social-unica', clusterNome: 'Prestação Social Única', tipo: 'pillar'},
  {url: '/psu-quando-entra-em-vigor.html',
   titulo: 'PSU 2026: o que já foi aprovado e o que ainda falta decidir',
   descricao: 'Timeline da PSU 2026: lei aprovada a 25/06/2026. Decreto-lei pendente (prazo PRR: 31 ago 2026). Entrada em vigor prevista para 1 jan 2027.',
   keywords: 'psu quando entra vigor decreto-lei prazo prr ago 2026 jan 2027 timeline',
   cluster: 'prestacao-social-unica', clusterNome: 'Prestação Social Única', tipo: 'artigo'},
  {url: '/psu-quem-tem-direito.html',
   titulo: 'Quem tem direito à PSU (condições de acesso aprovadas)',
   descricao: 'Condições de acesso à PSU aprovadas pelo Parlamento a 25/06/2026: 18+ anos, residência em Portugal, limite de património 60 × IAS.',
   keywords: 'psu quem tem direito condições acesso residência cidadania rendimento adultos equivalentes trabalho social',
   cluster: 'prestacao-social-unica', clusterNome: 'Prestação Social Única', tipo: 'artigo'},
  {url: '/psu-vs-abono-familia.html',
   titulo: 'PSU e Abono de Família: são apoios diferentes',
   descricao: 'O Abono de Família não integra a PSU e não é afectado pela sua entrada em vigor. São regimes totalmente distintos.',
   keywords: 'psu abono família diferença subsistema familiar excluído mantém csi',
   cluster: 'prestacao-social-unica', clusterNome: 'Prestação Social Única', tipo: 'artigo'},
  {url: '/psu-lista-13-apoios.html',
   titulo: 'As 13 prestações que a PSU vai substituir (lista completa)',
   descricao: 'Lista completa das 13 prestações sociais que a PSU vai substituir: RSI, subsídio social de desemprego, pensões sociais e outros apoios.',
   keywords: 'psu 13 prestações substituir lista rsi subsídio social desemprego pensão social regime transitório',
   cluster: 'prestacao-social-unica', clusterNome: 'Prestação Social Única', tipo: 'artigo'},
  {url: '/psu-trabalho-social.html',
   titulo: 'Trabalho social na PSU: aprovado vs. por definir',
   descricao: 'Até 15h/semana de atividades de solidariedade social na PSU: quem se aplica, quem está isento, e a disputa PS-PSD sobre a obrigatoriedade.',
   keywords: 'psu trabalho social solidariedade obrigatório facultativo 15 horas isento incapacidade amim',
   cluster: 'prestacao-social-unica', clusterNome: 'Prestação Social Única', tipo: 'artigo'},
  {url: '/p/habitacao.html',
   titulo: 'Apoios à Habitação em Portugal 2026',
   descricao: 'Porta 65 Jovem, Porta 65+ e o estado real do Apoio Extraordinário à Renda em 2026. Guia completo dos apoios ao arrendamento.',
   keywords: 'habitação arrendamento renda porta 65 apoio extraordinário cluster guia',
   cluster: 'habitacao', clusterNome: 'Habitação', tipo: 'pillar'},
  {url: '/porta-65.html',
   titulo: 'Porta 65 Jovem e Porta 65+ 2026',
   descricao: 'Apoio ao arrendamento para jovens até 35 anos ou qualquer idade com quebra de rendimentos. Candidaturas contínuas, sem prazo em 2026.',
   keywords: 'porta 65 jovem arrendamento renda apoio ihru candidatura sem prazo requisitos valores',
   cluster: 'habitacao', clusterNome: 'Habitação', tipo: 'artigo'},
  {url: '/apoio-extraordinario-renda.html',
   titulo: 'Apoio Extraordinário à Renda 2026: o que aconteceu e alternativas',
   descricao: 'Fechado a novos beneficiários desde 15-03-2023, com revogação anunciada mas ainda não publicada. Estado actual e alternativas.',
   keywords: 'apoio extraordinário renda paer fechado revogação alternativas arrendamento',
   cluster: 'habitacao', clusterNome: 'Habitação', tipo: 'artigo'},
  {url: '/simulador-abono.html',
   titulo: 'Simulador de Abono de Família 2026',
   descricao: 'Calculadora online do abono de família 2026. Simula o escalão e valor mensal com base no rendimento do agregado.',
   keywords: 'simulador abono família 2026 escalão rendimento referência calculadora',
   cluster: 'familia', clusterNome: 'Família e Crianças', tipo: 'ferramenta'},
  {url: '/simulador-ase.html',
   titulo: 'Simulador de Ação Social Escolar (ASE) 2026/2027',
   descricao: 'Calculadora do escalão ASE 2026/2027. Descobre a que categoria tens direito — refeições, material escolar, transportes.',
   keywords: 'simulador ase ação social escolar escalão rendimento refeições material transportes 2026',
   cluster: 'apoios-escolares', clusterNome: 'Apoios Escolares', tipo: 'ferramenta'},
  {url: '/simulador-csi.html',
   titulo: 'Simulador do Complemento Solidário para Idosos (CSI) 2026',
   descricao: 'Calculadora online do CSI 2026. Simula a estimativa mensal com base na idade, situação e rendimentos.',
   keywords: 'simulador csi complemento solidário idosos calculadora valor referência 2026',
   cluster: 'idosos-incapacidade-cuidadores', clusterNome: 'Idosos, Incapacidade e Cuidadores', tipo: 'ferramenta'},
  {url: '/simulador-subsidio-doenca.html',
   titulo: 'Simulador de Subsídio de Doença 2026',
   descricao: 'Calculadora online do subsídio de doença 2026, com desagregação por escalão (55% a 75%), dias de espera e majoração.',
   keywords: 'simulador subsídio doença calculadora baixa médica escalão percentagem cit',
   cluster: 'trabalho-rendimento', clusterNome: 'Trabalho e Rendimento', tipo: 'ferramenta'},
  {url: '/comecar-aqui.html',
   titulo: 'Começa aqui — encontra o teu apoio',
   descricao: 'Não sabes por onde começar? Responde a três perguntas e descobre os apoios sociais e direitos que podem aplicar-se ao teu caso.',
   keywords: 'comecar começar por onde apoio situação família trabalho estudar desemprego',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/simuladores.html',
   titulo: 'Simuladores e Calculadoras',
   descricao: 'Simuladores gratuitos de abono de família, Ação Social Escolar (ASE) e Complemento Solidário para Idosos (CSI).',
   keywords: 'simuladores calculadoras abono ase csi ferramentas hub',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/p/familia.html',
   titulo: 'Apoios para Família e Crianças 2026',
   descricao: 'Abono de família e licença parental (subsídio parental): valores, condições e simulador. Guia completo para quem tem filhos.',
   keywords: 'família crianças abono licença parental subsidio parental cluster guia',
   cluster: 'familia', clusterNome: 'Família e Crianças', tipo: 'pillar'},
  {url: '/p/idosos-incapacidade-cuidadores.html',
   titulo: 'Apoios para Idosos, Incapacidade e Cuidadores 2026',
   descricao: 'Complemento Solidário para Idosos (CSI), Estatuto do Cuidador Informal e AMIM: quem tem direito, valores e como pedir.',
   keywords: 'idosos incapacidade cuidadores csi complemento solidário cuidador informal amim cluster guia',
   cluster: 'idosos-incapacidade-cuidadores', clusterNome: 'Idosos, Incapacidade e Cuidadores', tipo: 'pillar'},
  {url: '/p/trabalho-rendimento.html',
   titulo: 'Apoios de Trabalho e Rendimento 2026',
   descricao: 'Subsídio de desemprego e RSI: condições, valores e como pedir. Guia completo para quem está sem trabalho ou com rendimentos baixos.',
   keywords: 'trabalho rendimento desemprego rsi subsidio cluster guia',
   cluster: 'trabalho-rendimento', clusterNome: 'Trabalho e Rendimento', tipo: 'pillar'},
  {url: '/noticias.html',
   titulo: 'Notícias',
   descricao: 'O que mudou nos apoios, direitos e burocracia em Portugal — notícias relevantes, com fonte verificada.',
   keywords: 'notícias novidades alterações apoios',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/sobre.html',
   titulo: 'Sobre o Tens Direito',
   descricao: 'Quem somos, metodologia e política de correções do Tens Direito — site informativo sobre apoios sociais e direitos em Portugal.',
   keywords: 'sobre quem somos metodologia independência correções',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/fontes.html',
   titulo: 'Fontes Oficiais',
   descricao: 'Lista das fontes oficiais utilizadas pelo Tens Direito: Diário da República, gov.pt, Segurança Social, IEFP e outras.',
   keywords: 'fontes oficiais diário república segurança social iefp gov.pt legislação',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/privacidade.html',
   titulo: 'Política de Privacidade',
   descricao: 'Política de privacidade e uso de cookies do Tens Direito. RGPD.',
   keywords: 'privacidade cookies rgpd dados pessoais',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/acessibilidade.html',
   titulo: 'Acessibilidade',
   descricao: 'Compromisso de acessibilidade do Tens Direito — WCAG 2.1 AA, como reportar barreiras.',
   keywords: 'acessibilidade wcag leitor de ecrã teclado contraste barreiras',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/documentos.html',
   titulo: 'Gerador de Documentos',
   descricao: 'Minutas de reclamações e cartas de acompanhamento para a Segurança Social, geradas no teu browser. Nada é enviado nem guardado.',
   keywords: 'gerador documentos minuta requerimento reclamação carta modelo segurança social',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/documentos/reclamacao-decisao-seguranca-social.html',
   titulo: 'Reclamação de decisão da Segurança Social',
   descricao: 'Indeferimento ou valor errado da Segurança Social? Gera uma minuta de reclamação grátis — preenche os campos e recebe o texto pronto.',
   keywords: 'reclamação indeferimento segurança social minuta requerimento cpa recurso hierárquico',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/documentos/carta-acompanhamento-csi.html',
   titulo: 'Carta de acompanhamento — pedido de CSI',
   descricao: 'Carta grátis para acompanhar o Mod. CSI 1 – DGSS ao pedir o Complemento Solidário para Idosos. Não substitui o formulário oficial.',
   keywords: 'csi carta acompanhamento mod csi 1 complemento solidário idosos requerimento',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/documentos/carta-acompanhamento-reavaliacao-abono.html',
   titulo: 'Carta de acompanhamento — reavaliação do escalão do abono',
   descricao: 'Carta grátis para acompanhar o pedido de reavaliação do escalão do abono de família — complemento ao pedido online na Segurança Social Direta.',
   keywords: 'abono reavaliação escalão carta acompanhamento gf58 modelo requerimento',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/documentos/recurso-hierarquico-seguranca-social.html',
   titulo: 'Recurso hierárquico de decisão da Segurança Social',
   descricao: 'Gera uma minuta de recurso hierárquico de uma decisão da Segurança Social, para quando a reclamação não resolveu ou queres avançar directamente.',
   keywords: 'recurso hierárquico segurança social minuta requerimento cpa superior',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/documentos/exposicao-atraso-processamento.html',
   titulo: 'Exposição por atraso no processamento de prestação',
   descricao: 'Gera uma exposição a pedir decisão urgente quando um pedido à Segurança Social ultrapassa o prazo legal de 90 dias.',
   keywords: 'exposição atraso demora prazo prestação segurança social dever de decisão cpa',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/documentos/carta-acompanhamento-divida-prestacoes.html',
   titulo: 'Carta de acompanhamento — dívida em prestações',
   descricao: 'Gera uma carta para acompanhar o pedido de plano prestacional de dívida à Segurança Social. Não substitui o formulário oficial.',
   keywords: 'dívida segurança social prestações plano prestacional requerimento execução fiscal',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/documentos/carta-acompanhamento-svi-recurso.html',
   titulo: 'Carta de acompanhamento — recurso de decisão do SVI',
   descricao: 'Gera uma carta para acompanhar o Mod. SVI 55-DGSS de recurso a uma decisão do Sistema de Verificação de Incapacidades. Prazo de 10 dias.',
   keywords: 'svi sistema verificação incapacidades junta médica recurso carta acompanhamento',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/documentos/carta-acompanhamento-comunicacao-alteracao.html',
   titulo: 'Carta de acompanhamento — alteração de morada, agregado ou rendimentos',
   descricao: 'Gera uma carta para comunicar por escrito uma alteração de morada, agregado familiar ou rendimentos à Segurança Social.',
   keywords: 'comunicação alteração agregado familiar morada rendimentos carta segurança social',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/documentos/requerimento-reavaliacao-escalao-ase.html',
   titulo: 'Pedido de reavaliação do escalão de ASE',
   descricao: 'Gera um requerimento para pedir a reavaliação do escalão de Ação Social Escolar (ASE) à escola, quando o rendimento familiar baixa.',
   keywords: 'ase reavaliação escalão requerimento escola agrupamento ação social escolar',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/documentos/pedido-acesso-documentos-administrativos.html',
   titulo: 'Pedido de acesso a documentos administrativos (LADA)',
   descricao: 'Gera um pedido de consulta do teu processo ou de acesso a documentos administrativos, ao abrigo da Lei n.º 26/2016 (LADA).',
   keywords: 'acesso documentos administrativos lada consulta processo cada requerimento',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/documentos/requerimento-generico-seguranca-social.html',
   titulo: 'Requerimento genérico à Segurança Social',
   descricao: 'Gera um requerimento genérico à Segurança Social para situações não cobertas por um modelo específico: identificação, exposição e pedido.',
   keywords: 'requerimento genérico segurança social modelo base petição',
   cluster: null, clusterNome: null, tipo: null},
  {url: '/documentos/pedido-declaracao-comprovativo-prestacoes.html',
   titulo: 'Pedido de declaração/comprovativo de prestações',
   descricao: 'Gera um pedido escrito de declaração de situação contributiva ou comprovativo de uma prestação social.',
   keywords: 'declaração situação contributiva comprovativo prestação social pedido',
   cluster: null, clusterNome: null, tipo: null}
];

var MIN_CARACTERES = 2;
var MAX_RESULTADOS = 8;
var RAIO_EXCERTO = 30;

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, function(c) {
    return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c];
  });
}

// Destaca a 1.ª ocorrência do termo, sem truncar — usado no título
// (o título mostra-se sempre inteiro, nunca cortado).
function destacarCompleto(texto, termoLower) {
  var idx = texto.toLowerCase().indexOf(termoLower);
  if (idx === -1) return escapeHtml(texto);
  return escapeHtml(texto.slice(0, idx)) +
    '<mark>' + escapeHtml(texto.slice(idx, idx + termoLower.length)) + '</mark>' +
    escapeHtml(texto.slice(idx + termoLower.length));
}

// Excerto curto à volta da 1.ª ocorrência do termo, com reticências
// quando corta texto — usado quando o título não contém o termo, para
// mostrar ao utilizador ONDE é que a página corresponde à pesquisa.
function construirExcerto(texto, termoLower) {
  if (!texto) return '';
  var idx = texto.toLowerCase().indexOf(termoLower);
  if (idx === -1) {
    var corte = texto.slice(0, 90);
    return escapeHtml(corte) + (texto.length > 90 ? '…' : '');
  }
  var inicio = Math.max(0, idx - RAIO_EXCERTO);
  var fim = Math.min(texto.length, idx + termoLower.length + RAIO_EXCERTO);
  return (inicio > 0 ? '…' : '') +
    escapeHtml(texto.slice(inicio, idx)) +
    '<mark>' + escapeHtml(texto.slice(idx, idx + termoLower.length)) + '</mark>' +
    escapeHtml(texto.slice(idx + termoLower.length, fim)) +
    (fim < texto.length ? '…' : '');
}

// Camadas de relevância: 1) título, 2) início/corpo da descrição,
// 3) keywords indexadas — nunca misturadas sem ordem, para que
// "sub" não devolva a mesma desordem de sempre entre título e
// keywords. Dentro de cada camada, ordem alfabética (determinística).
function pesquisar(termo) {
  var t = (termo || '').toLowerCase().trim();
  if (t.length < MIN_CARACTERES) return [];

  var encontrados = [];
  paginas.forEach(function(p) {
    var tituloLower = p.titulo.toLowerCase();
    var descLower = (p.descricao || '').toLowerCase();
    var kwLower = p.keywords.toLowerCase();

    var camada = null;
    if (tituloLower.indexOf(t) !== -1) camada = 1;
    else if (descLower.indexOf(t) !== -1) camada = 2;
    else if (kwLower.indexOf(t) !== -1) camada = 3;
    if (camada === null) return;

    var tituloHtml, excertoHtml;
    if (camada === 1) {
      tituloHtml = destacarCompleto(p.titulo, t);
      excertoHtml = p.descricao
        ? escapeHtml(p.descricao.slice(0, 90)) + (p.descricao.length > 90 ? '…' : '')
        : '';
    } else {
      tituloHtml = escapeHtml(p.titulo);
      excertoHtml = construirExcerto(camada === 2 ? p.descricao : p.keywords, t);
    }

    encontrados.push({
      url: p.url,
      titulo: p.titulo,
      tituloHtml: tituloHtml,
      excertoHtml: excertoHtml,
      cluster: p.cluster || null,
      clusterNome: p.clusterNome || null,
      tipo: p.tipo || null,
      camada: camada
    });
  });

  encontrados.sort(function(a, b) {
    if (a.camada !== b.camada) return a.camada - b.camada;
    return a.titulo.localeCompare(b.titulo, 'pt');
  });

  return encontrados.slice(0, MAX_RESULTADOS);
}

function mostrarResultados(resultados, termo, idResultados) {
  var div = document.getElementById(idResultados || 'resultados-pesquisa');
  if (!div) return;
  var t = (termo || '').trim();

  if (t.length < MIN_CARACTERES) {
    div.style.display = 'none';
    div.innerHTML = '';
    return;
  }

  if (!resultados.length) {
    div.innerHTML =
      '<div class="resultado-vazio">' +
        '<p>Sem resultados para “' + escapeHtml(t) + '”.</p>' +
        '<a href="/#guias-de-apoios">Vê todos os guias →</a>' +
      '</div>';
  } else {
    div.innerHTML = resultados.map(function(r) {
      var badges = '';
      if (r.clusterNome) badges += '<span class="resultado-badge">' + escapeHtml(r.clusterNome) + '</span>';
      if (r.tipo === 'ferramenta') badges += '<span class="resultado-badge resultado-badge-ferramenta">Ferramenta</span>';
      return '<a href="' + r.url + '" class="resultado-item">' +
        '<span class="resultado-titulo">' + r.tituloHtml + '</span>' +
        (r.excertoHtml ? '<span class="resultado-excerto">' + r.excertoHtml + '</span>' : '') +
        (badges ? '<span class="resultado-badges">' + badges + '</span>' : '') +
      '</a>';
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

// ── calc-apoios.js — lógica de cálculo partilhada entre simuladores ────────
// Extraído de simulador-abono.html (2026-07-27, fundação do verificador
// multi-apoio) — refactor puro de "mover código", lógica idêntica à que
// vivia inline na página. Módulo de lógica pura: NUNCA contém valores
// legais hardcoded — recebe sempre `config`/`params` como argumento, lidos
// em runtime de /dados/parametros.json pelo loader de cada página (ver
// carregarParametrosAbono() em simulador-abono.html). Script clássico (sem
// type="module"), por isso as funções ficam automaticamente no âmbito
// global — os testes Playwright continuam a chamá-las via
// page.evaluate/window, exactamente como quando viviam inline.

// ── Abono de família ─────────────────────────────────────────────────────
// Funções puras, testadas em tests/test_simulador_abono_calculo.py.
function getEscalao(config, rr) {
  for (const escalao of config.escaloes) {
    if (rr <= escalao.limite) return escalao;
  }
  return config.escaloes[config.escaloes.length - 1];
}

function getValorPorIdade(escalaoObj, idadesMeses) {
  if (escalaoObj.id === 5) return 0;
  let valor = 0;
  idadesMeses.forEach(idade => {
    if (idade <= 36) valor += escalaoObj.valores.a36;
    else if (idade <= 72) valor += escalaoObj.valores.a72;
    else valor += escalaoObj.valores.mais72;
  });
  return valor;
}

function calcularAbonoValor(config, input) {
  const { rendimentoAnual, numCriancas, idadesMeses, monoparental } = input;
  const rr = rendimentoAnual / (numCriancas + 1);
  const escalaoObj = getEscalao(config, rr);
  let valorBase = getValorPorIdade(escalaoObj, idadesMeses);

  let garantiaAplicada = false;
  if (escalaoObj.id === 1 && rr < config.limiteGarantia) {
    const minimo = config.garantiaInfancia * numCriancas;
    if (minimo > valorBase) {
      valorBase = minimo;
      garantiaAplicada = true;
    }
  }

  const majoracao = monoparental ? valorBase * config.majoracaoMonoparentalFracao : 0;
  const valorTotal = valorBase + majoracao;

  return {
    rr, escalao: escalaoObj.id, nomeEscalao: escalaoObj.nome, cor: escalaoObj.cor,
    valorBase, majoracao, valorTotal, garantiaAplicada,
  };
}

// ── Motor de avaliação de apoios (avaliarApoios) ────────────────────────────
// PR 3 da série "simulador universal" (dados/condicoes/*.yaml compilados por
// scripts/gerar_condicoes_json.py em dados/condicoes.json). Função pura,
// testada em tests/test_avaliar_apoios_calculo.py — recebe o
// dados/condicoes.json já carregado e as respostas dadas até agora (que
// podem estar incompletas: é assim que se consegue excluir um apoio antes
// de perguntar tudo, em vez de forçar o formulário inteiro primeiro).
//
// Estado por apoio: "elegivel" | "inelegivel" | "indeterminado".
// "indeterminado" só acontece quando falta responder a uma pergunta que
// ainda pode mudar o resultado — nunca por omissão silenciosa, e vem
// sempre acompanhado de perguntasEmFalta, para o chamador (a página do
// PR 11) saber exactamente o que ainda falta perguntar.

function idadeMesesTotais(dataNascimentoISO, hojeISO) {
  const nascimento = new Date(dataNascimentoISO);
  const hoje = new Date(hojeISO);
  let meses = (hoje.getFullYear() - nascimento.getFullYear()) * 12 + (hoje.getMonth() - nascimento.getMonth());
  if (hoje.getDate() < nascimento.getDate()) meses -= 1;
  return meses;
}

function idadeAnosCompletos(dataNascimentoISO, hojeISO) {
  return Math.floor(idadeMesesTotais(dataNascimentoISO, hojeISO) / 12);
}

function compararValores(valorResposta, operador, valorAlvo) {
  switch (operador) {
    case 'eq': return valorResposta === valorAlvo;
    case 'neq': return valorResposta !== valorAlvo;
    case 'gte': return valorResposta >= valorAlvo;
    case 'lte': return valorResposta <= valorAlvo;
    case 'gt': return valorResposta > valorAlvo;
    case 'lt': return valorResposta < valorAlvo;
    default: throw new Error(`operador_comparacao desconhecido: ${operador}`);
  }
}

function juntarPerguntasEmFalta(resultados) {
  const todas = [];
  resultados.forEach(r => { if (r.perguntasEmFalta) todas.push(...r.perguntasEmFalta); });
  return [...new Set(todas)];
}

// Fórmulas de condição — PR 6. Uma fórmula precisa de mais do que um
// campo de resposta (ao contrário de uma folha normal), por isso tem a
// sua própria avaliação em vez de reusar compararValores(). Extensível:
// acrescentar uma fórmula nova é um novo `case`, nunca alterar as
// existentes.
function avaliarFormula(condicao, respostas) {
  if (condicao.formula === 'escala_equivalencia_rsi') {
    const campos = [condicao.campo_rendimento, condicao.campo_adultos_adicionais, condicao.campo_menores];
    const emFalta = campos.filter(c => respostas[c] === undefined || respostas[c] === null || respostas[c] === '');
    if (emFalta.length > 0) {
      return { estado: 'indeterminado', perguntasEmFalta: emFalta };
    }
    const rendimento = respostas[condicao.campo_rendimento];
    const adultosAdicionais = respostas[condicao.campo_adultos_adicionais];
    const menores = respostas[condicao.campo_menores];
    const limiar = condicao.valor_titular
      + adultosAdicionais * condicao.valor_adulto_adicional
      + menores * condicao.valor_menor;
    return { estado: rendimento <= limiar ? 'elegivel' : 'inelegivel' };
  }
  if (condicao.formula === 'psu_valor_positivo') {
    // Réplica da mecânica de calcularPSU() de simulador-psu.html (PSUglobal =
    // PSUbase + CIT − rendimentos, com mínimo). Paridade garantida por
    // tests/test_avaliar_apoios_psu_paridade.py — se as duas divergirem, o
    // teste falha. Não modela majorações (artigos 26.º/27.º) nem o art. 17.º.
    const campos = [
      condicao.campo_rendimento_trabalho,
      condicao.campo_outros_rendimentos,
      condicao.campo_adultos_adicionais,
      condicao.campo_menores,
    ];
    const emFalta = campos.filter(c => respostas[c] === undefined || respostas[c] === null || respostas[c] === '');
    if (emFalta.length > 0) {
      return { estado: 'indeterminado', perguntasEmFalta: emFalta };
    }
    const trabalho = respostas[condicao.campo_rendimento_trabalho];
    const outros = respostas[condicao.campo_outros_rendimentos];
    const adultosAdicionais = respostas[condicao.campo_adultos_adicionais];
    const menores = respostas[condicao.campo_menores];

    const adultosEquivalentes = condicao.ponderacao_titular
      + adultosAdicionais * condicao.ponderacao_maior
      + menores * condicao.ponderacao_menor;
    const psuBase = condicao.valor_referencia * adultosEquivalentes;
    const cit = Math.min(trabalho, condicao.cit_limiar)
      + condicao.cit_taxa * Math.max(0, trabalho - condicao.cit_limiar);
    const psuGlobal = Math.max(0, psuBase + cit - (trabalho + outros));
    return { estado: psuGlobal >= condicao.valor_minimo ? 'elegivel' : 'inelegivel' };
  }
  throw new Error(`fórmula desconhecida: ${condicao.formula}`);
}

// Avalia uma condição ou grupo (mesma forma recursiva de
// dados/condicoes.json — um nó com `condicoes` é sempre um grupo, nunca
// tem `campo` próprio; um nó sem `condicoes` é sempre uma folha).
function avaliarCondicao(condicao, respostas, hojeISO) {
  if (condicao.condicoes) {
    const resultados = condicao.condicoes.map(c => avaliarCondicao(c, respostas, hojeISO));

    if (condicao.operador === 'any') {
      if (resultados.some(r => r.estado === 'elegivel')) return { estado: 'elegivel' };
      if (resultados.some(r => r.estado === 'indeterminado')) {
        return { estado: 'indeterminado', perguntasEmFalta: juntarPerguntasEmFalta(resultados) };
      }
      return { estado: 'inelegivel' };
    }

    // all
    if (resultados.some(r => r.estado === 'inelegivel')) return { estado: 'inelegivel' };
    if (resultados.some(r => r.estado === 'indeterminado')) {
      return { estado: 'indeterminado', perguntasEmFalta: juntarPerguntasEmFalta(resultados) };
    }
    return { estado: 'elegivel' };
  }

  if (condicao.tipo === 'formula') {
    return avaliarFormula(condicao, respostas);
  }

  let valorResposta = respostas[condicao.campo];
  if (valorResposta === undefined || valorResposta === null || valorResposta === '') {
    return { estado: 'indeterminado', perguntasEmFalta: [condicao.campo] };
  }

  if (condicao.unidade_comparacao === 'meses_totais') {
    valorResposta = idadeMesesTotais(valorResposta, hojeISO);
  } else if (condicao.unidade_comparacao === 'anos') {
    valorResposta = idadeAnosCompletos(valorResposta, hojeISO);
  }

  const cumpre = compararValores(valorResposta, condicao.operador_comparacao, condicao.valor);
  return { estado: cumpre ? 'elegivel' : 'inelegivel' };
}

function avaliarApoios(condicoesJson, respostas, hojeISO) {
  hojeISO = hojeISO || new Date().toISOString().slice(0, 10);
  const resultado = {};
  for (const [apoioId, apoio] of Object.entries(condicoesJson.apoios)) {
    resultado[apoioId] = avaliarCondicao(
      { operador: apoio.operador, condicoes: apoio.condicoes },
      respostas,
      hojeISO
    );
    // Marca de substituição (ex.: RSI → PSU): não altera o estado, só informa
    // a página de que, a partir da data indicada, vale o apoio substituto.
    if (apoio.substituido_por) {
      resultado[apoioId].substituidoPor = apoio.substituido_por;
      resultado[apoioId].substituidoAPartirDe = apoio.substituido_a_partir_de;
    }
  }
  return resultado;
}

// ── Próxima pergunta do assistente (proximaPergunta) ────────────────────────
// PR 11 da série "simulador universal" (simulador-universal.html). Função
// pura, testada em tests/test_avaliar_apoios_calculo.py. Recebe o mesmo
// dados/condicoes.json e as respostas dadas até agora; devolve o nome do
// campo a perguntar a seguir, ou null quando já não há nenhuma pergunta
// aplicável que ainda possa mudar um resultado.
//
// Regras (por esta ordem):
//   1. Só contam campos que aparecem em perguntasEmFalta de um apoio ainda
//      "indeterminado" — apoios já decididos (elegivel/inelegivel) não
//      contam, e um campo que já não pode mudar nada nunca é perguntado.
//   2. Só perguntas aplicáveis (aplicavel_se) ainda sem resposta. Um campo
//      cuja pergunta-mãe ainda não foi respondida "sobe" para a pergunta-mãe
//      (ex.: as perguntas da criança puxam tem_filhos_a_cargo); se a mãe já
//      foi respondida com outro valor, o campo simplesmente não se pergunta.
//   3. Escalões: perguntas sobre o requerente primeiro, depois as da criança
//      (aplicavel_se em tem_filhos_a_cargo — referem-se sempre ao filho mais
//      novo), e os campos monetários (unidade em EUR) sempre no fim.
//   4. Dentro do escalão, o campo presente em mais apoios indeterminados (o
//      que mais ajuda a decidir); desempate estável pela ordem de
//      perguntas.yaml, nunca pela ordem das respostas.

const CAMPO_FILHOS_A_CARGO = 'tem_filhos_a_cargo';

function respostaDada(respostas, campo) {
  const v = respostas[campo];
  return v !== undefined && v !== null && v !== '';
}

// Devolve o campo que de facto se deve perguntar para chegar a `campo`
// (o próprio, ou a pergunta-mãe ainda por responder), ou null se `campo`
// não é aplicável com as respostas actuais.
function campoAPerguntar(perguntas, respostas, campo) {
  const vistos = new Set();
  let atual = campo;
  for (;;) {
    if (vistos.has(atual)) return null; // ciclo — nunca deve acontecer (guardrail no compilador)
    vistos.add(atual);
    const def = perguntas[atual];
    if (!def) return null;
    const cond = def.aplicavel_se;
    if (!cond) return atual;
    if (!respostaDada(respostas, cond.campo)) {
      atual = cond.campo;
      continue;
    }
    return respostas[cond.campo] === cond.valor ? atual : null;
  }
}

function escalaoPergunta(def) {
  if (def.unidade && String(def.unidade).indexOf('EUR') !== -1) return 2;
  if (def.aplicavel_se && def.aplicavel_se.campo === CAMPO_FILHOS_A_CARGO) return 1;
  return 0;
}

function proximaPergunta(condicoesJson, respostas, hojeISO) {
  const perguntas = condicoesJson.perguntas || {};
  const ordem = Object.keys(perguntas);
  const avaliacao = avaliarApoios(condicoesJson, respostas, hojeISO);

  const contagem = {};
  for (const r of Object.values(avaliacao)) {
    if (r.estado !== 'indeterminado') continue;
    const candidatosDoApoio = new Set();
    (r.perguntasEmFalta || []).forEach(campo => {
      const alvo = campoAPerguntar(perguntas, respostas, campo);
      if (alvo && !respostaDada(respostas, alvo)) candidatosDoApoio.add(alvo);
    });
    candidatosDoApoio.forEach(c => { contagem[c] = (contagem[c] || 0) + 1; });
  }

  const candidatos = Object.keys(contagem);
  if (candidatos.length === 0) return null;
  candidatos.sort((a, b) => {
    const ea = escalaoPergunta(perguntas[a]);
    const eb = escalaoPergunta(perguntas[b]);
    if (ea !== eb) return ea - eb;
    if (contagem[a] !== contagem[b]) return contagem[b] - contagem[a];
    return ordem.indexOf(a) - ordem.indexOf(b);
  });
  return candidatos[0];
}

// Campos respondidos que fizeram um apoio falhar — para a página explicar
// o "porquê" de um "Não tens direito" sem inventar texto: devolve os
// campos das condições de topo que ficaram "inelegivel", pela ordem em
// que aparecem no apoio.
function camposQueExcluem(apoio, respostas, hojeISO) {
  hojeISO = hojeISO || new Date().toISOString().slice(0, 10);
  const campos = [];
  const recolher = (c) => {
    if (c.condicoes) { c.condicoes.forEach(recolher); return; }
    const lista = c.tipo === 'formula'
      ? Object.keys(c).filter(k => k.indexOf('campo_') === 0).map(k => c[k])
      : [c.campo];
    lista.forEach(campo => {
      if (respostaDada(respostas, campo) && campos.indexOf(campo) === -1) campos.push(campo);
    });
  };
  apoio.condicoes.forEach(c => {
    if (avaliarCondicao(c, respostas, hojeISO).estado === 'inelegivel') recolher(c);
  });
  return campos;
}

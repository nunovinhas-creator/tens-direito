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
  }
  return resultado;
}

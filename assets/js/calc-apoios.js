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

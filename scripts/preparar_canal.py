"""
Prepara o rascunho diário do canal de WhatsApp — nunca publica.

Dois gatilhos, por ordem de prioridade (ver CLAUDE.md → "CANAL DE
WHATSAPP — GATILHO EDITORIAL DE PUBLICAÇÃO"). Deliberadamente só dois —
o gatilho de "notícia relevante" ficou por construir (medição real de
agosto de 2026 mostrou ~20 dias/mês com pelo menos uma vencedora do
gerar_noticias.py, dos quais só 2 tinham sinal legal directo no título
— e esses 2 já coincidiam com o gatilho 1). Ver ROADMAP.md → "À espera
de um sinal" → "Canal de WhatsApp" para o raciocínio completo antes de
o reabrir.

1. ALTERAÇÃO LEGAL CONFIRMADA — data/canal_pendente.json
   (`{"_nota": "...", "entradas": [{"titulo", "resumo", "paginas": [...]}]}`)
   é uma fila preenchida à MÃO por uma sessão editorial, no mesmo commit
   em que corrige uma página por causa de um facto legal confirmado
   (nunca por refactor/limpeza/reorganização — mesma regra já
   documentada em CLAUDE.md). O campo `_nota` explica o mecanismo
   directamente no ficheiro (mesmo padrão de data/destaque_evento.json)
   e é preservado em todas as escritas deste script — nunca apagado
   numa reescrita automática. Este script NUNCA decide sozinho se algo
   é "uma alteração real" — só formata e entrega o que um humano já
   decidiu e escreveu. É deliberado que a fila não seja preenchida por
   nenhuma automação: o critério ("verificação manual confirma
   alteração real") é, por desenho, um passo humano.

2. CALENDÁRIO DE PAGAMENTOS — UMA mensagem por mês, a partir do
   primeiro dia útil, com as datas do mês inteiro, geradas de
   data/calendario_pagamentos.json (fonte já verificada por
   scripts/atualizar_calendario.py / scripts/scraper_calendario.py).
   Nunca um aviso por cada dia de pagamento. "Dia útil" é simplificado
   a segunda-sexta (sem calendário de feriados portugueses — o
   repositório não tem um noutro lado nenhum; documentado aqui como
   limitação conhecida, nunca escondida).

Regra de volume: no máximo 1 rascunho/dia. Se os dois gatilhos tiverem
algo pendente no mesmo dia, a alteração legal ganha — o calendário fica
em espera (não é descartado: `calendario_devido()` continua a devolver
o mês enquanto não for entregue, por isso a corrida seguinte sem
alteração legal pendente entrega-o).

Saída: escreve /tmp/canal_rascunho_hoje.json (efémero, fora do
repositório, nunca commitado) para o step de Issues do workflow
consumir. Sem nada a publicar hoje, não escreve nada — silêncio é o
comportamento correcto (mesma regra de honestidade já aplicada ao
resto do site, ver CLAUDE.md → "FRESCURA DA HOMEPAGE").

Risco residual documentado, aceite por desenho: se o passo de criação
da Issue falhar por um motivo transitório DEPOIS deste script já ter
consumido a entrada da fila / marcado o mês como entregue, essa
mensagem específica fica por publicar sem retry automático (o estado já
foi commitado). Dado tratar-se de uma ferramenta de sugestão, não de um
sistema crítico, este risco foi considerado aceitável em vez de
construir semântica "exactamente uma vez" à volta de uma chamada de API
que falha raramente — nunca escondido, registado aqui e em CLAUDE.md.

Uso (corrido pelo pipeline-diario.yml, sempre antes do push diário):
    python3 scripts/preparar_canal.py
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Optional

RAIZ_MODULO = Path(__file__).resolve().parent.parent
SAIDA_OMISSAO = Path("/tmp/canal_rascunho_hoje.json")

DOMINIO = "https://tensdireito.com"

sys.path.insert(0, str(RAIZ_MODULO / "scripts"))
from atualizar_calendario import MESES_PT, PRESTACOES  # noqa: E402


def _carregar_json(caminho: Path, omissao):
    if not caminho.exists():
        return omissao
    try:
        conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"AVISO: {caminho} inválido ({e}) — a tratar como vazio")
        return omissao
    return conteudo


def _guardar_json(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _carregar_fila_pendente(caminho: Path) -> dict:
    """
    Devolve o documento inteiro de data/canal_pendente.json — nunca só a
    lista de entradas. `{"_nota": "...", "entradas": [...]}`, mesmo
    padrão de data/destaque_evento.json (nota explicativa como campo
    normal do JSON, para nunca desaparecer numa reescrita automática —
    lição real de 12 dias de instruções não lidas nesse ficheiro).
    Uma forma inesperada (lista solta antiga, chave em falta) é tratada
    como vazia, com aviso, nunca um crash.
    """
    dados = _carregar_json(caminho, {"entradas": []})
    if not isinstance(dados, dict) or not isinstance(dados.get("entradas"), list):
        print(
            f"AVISO: {caminho} não tem a forma esperada "
            '({"_nota": ..., "entradas": [...]}) — a tratar como vazio'
        )
        return {"entradas": []}
    return dados


def obter_pendente_legal(fila: list) -> tuple[dict | None, list]:
    """
    Devolve (entrada, fila_restante). A entrada é a mais antiga da fila
    com um `resumo` não vazio — entradas malformadas antes dela são
    descartadas com aviso (nunca bloqueiam a fila para sempre), nunca
    silenciosamente.
    """
    restante = list(fila)
    while restante:
        candidata = restante.pop(0)
        if not isinstance(candidata, dict) or not str(candidata.get("resumo", "")).strip():
            print(f"AVISO: entrada malformada em canal_pendente.json descartada: {candidata!r}")
            continue
        return candidata, restante
    return None, restante


def calendario_devido(hoje: dt.date, estado: dict, dados_calendario: dict) -> dict | None:
    """
    Devolve os dados do mês corrente se o calendário mensal ainda não
    foi entregue este mês, hoje for dia útil (seg-sex) e o mês corrente
    já estiver presente em data/calendario_pagamentos.json — nunca
    antes disso, para nunca inventar um mês que a fonte oficial ainda
    não confirmou (mesmo invariante de `atualizar_calendario.py`: um
    mês sem dados degrada para "consultar a fonte oficial", nunca uma
    tabela inventada).
    """
    mes_corrente = f"{hoje.year:04d}-{hoje.month:02d}"
    if estado.get("ultimo_calendario_publicado") == mes_corrente:
        return None
    if hoje.weekday() >= 5:  # sábado(5)/domingo(6) — nunca no fim-de-semana
        return None
    for m in dados_calendario.get("meses", []):
        if m.get("ano") == hoje.year and m.get("mes") == hoje.month:
            return m
    return None


def formatar_rascunho_legal(entrada: dict) -> str:
    linhas = [str(entrada.get("resumo", "")).strip()]
    paginas = entrada.get("paginas") or []
    if paginas:
        links = " · ".join(f"{DOMINIO}/{p}" for p in paginas)
        linhas.append(links)
    return "\n\n".join(linha for linha in linhas if linha)


def formatar_rascunho_calendario(mes_dados: dict) -> str:
    nome_mes = MESES_PT[mes_dados["mes"]]
    linhas = [
        f"📅 Calendário de pagamentos da Segurança Social — {nome_mes} de {mes_dados['ano']}",
        "",
    ]
    for p in sorted(mes_dados.get("pagamentos", []), key=lambda x: x.get("dia", 0)):
        nomes = " + ".join(PRESTACOES.get(s, s) for s in p.get("prestacoes", []))
        linhas.append(f"• dia {p.get('dia')}: {nomes}")
    linhas.append("")
    linhas.append(
        f"Calendário completo: {DOMINIO}/calendario-pagamentos-seguranca-social.html"
    )
    return "\n".join(linhas)


def main(
    *,
    raiz: Optional[Path] = None,
    hoje: Optional[str] = None,
    saida: Optional[Path] = None,
) -> Optional[dict]:
    """
    Devolve o rascunho preparado (ou None se não houver nada a publicar
    hoje) — o mesmo dicionário escrito em `saida`. `raiz`/`hoje`/`saida`
    são sempre opcionais (produção usa os valores reais); testes passam
    um `tmp_path` e uma data fixa, sem monkeypatch.
    """
    raiz = raiz or RAIZ_MODULO
    hoje_data = (
        dt.date.fromisoformat(hoje) if hoje else dt.datetime.now(dt.timezone.utc).date()
    )
    saida = saida or SAIDA_OMISSAO

    caminho_pendente = raiz / "data" / "canal_pendente.json"
    caminho_estado = raiz / "data" / "canal_estado.json"
    caminho_calendario = raiz / "data" / "calendario_pagamentos.json"

    estado = _carregar_json(caminho_estado, {})
    documento_pendente = _carregar_fila_pendente(caminho_pendente)
    fila = documento_pendente["entradas"]

    entrada, resto = obter_pendente_legal(fila)
    if resto != fila:
        # Só o campo "entradas" muda — "_nota" (e qualquer outra chave)
        # sobrevive intacta, nunca reescrita a partir do zero.
        documento_pendente["entradas"] = resto
        _guardar_json(caminho_pendente, documento_pendente)

    if entrada is not None:
        rascunho = {
            "gatilho": "alteracao_legal",
            "titulo": str(entrada.get("titulo") or "Alteração legal confirmada"),
            "texto": formatar_rascunho_legal(entrada),
            "data": hoje_data.isoformat(),
        }
        estado["ultima_entrega_canal"] = hoje_data.isoformat()
        _guardar_json(caminho_estado, estado)
        _guardar_json(saida, rascunho)
        print(f"Rascunho preparado (alteração legal): {rascunho['titulo']}")
        return rascunho

    dados_calendario = _carregar_json(caminho_calendario, {})
    mes_dados = calendario_devido(hoje_data, estado, dados_calendario)
    if mes_dados is not None:
        rascunho = {
            "gatilho": "calendario",
            "titulo": f"Calendário de pagamentos — {MESES_PT[mes_dados['mes']]} de {mes_dados['ano']}",
            "texto": formatar_rascunho_calendario(mes_dados),
            "data": hoje_data.isoformat(),
        }
        estado["ultimo_calendario_publicado"] = f"{hoje_data.year:04d}-{hoje_data.month:02d}"
        estado["ultima_entrega_canal"] = hoje_data.isoformat()
        _guardar_json(caminho_estado, estado)
        _guardar_json(saida, rascunho)
        print(f"Rascunho preparado (calendário): {mes_dados['mes']}/{mes_dados['ano']}")
        return rascunho

    print("Nada a publicar no canal hoje.")
    return None


if __name__ == "__main__":
    main()

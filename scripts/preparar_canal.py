"""
Prepara o rascunho diário do canal de WhatsApp — nunca publica.

Gatilhos, por ordem de prioridade (ver CLAUDE.md → "CANAL DE WHATSAPP —
GATILHO EDITORIAL DE PUBLICAÇÃO" → "Mecanismo"). O gatilho de "notícia
relevante" ficou deliberadamente por construir — medição real de agosto
de 2026 mostrou ~20 dias/mês com pelo menos uma vencedora do
gerar_noticias.py, dos quais só 2 tinham sinal legal directo no título
— e esses 2 já coincidiam com o gatilho 1. Ver ROADMAP.md → "À espera
de um sinal" → "Canal de WhatsApp" para o raciocínio completo antes de
o reabrir.

1a. ALTERAÇÃO LEGAL CONFIRMADA — data/canal_pendente.json
    (`{"_nota": "...", "entradas": [{"titulo", "resumo", "paginas": [...]}]}`)
    é uma fila preenchida à MÃO por uma sessão editorial, no mesmo
    commit em que corrige uma página por causa de um facto legal
    confirmado (nunca por refactor/limpeza/reorganização — mesma regra
    já documentada em CLAUDE.md). O campo `_nota` explica o mecanismo
    directamente no ficheiro (mesmo padrão de data/destaque_evento.json)
    e é preservado em todas as escritas deste script — nunca apagado
    numa reescrita automática. Este script NUNCA decide sozinho se algo
    é "uma alteração real" — só formata e entrega o que um humano já
    decidiu e escreveu. Produz um rascunho `confirmado: true`.

1b. ALTERAÇÃO LEGAL POR CONFIRMAR — caminho automático, sem fila
    manual: quando um dos 5 sentinelas dirigidos (`dre_psu`,
    `dre_psu_regulamentacao`, `dre_habitacao_paer`,
    `dre_habitacao_garantia`, `dre_ias` — ver `SENTINELAS_DIRIGIDOS`)
    escreve a sua chave de aviso em `data/scraped/avisos.log` no dia de
    hoje, este script prepara logo um rascunho — sem esperar que uma
    sessão editorial confirme e preencha 1a primeiro. Nunca confunde-se
    com 1a: o rascunho nasce `confirmado: false` e o texto nunca é
    pronto a copiar — é só o excerto bruto detectado em dre.pt, a
    aguardar verificação humana contra a fonte oficial antes de
    qualquer publicação (o próprio step de Issues do workflow escreve o
    aviso "NÃO PUBLICAR AINDA" no corpo, ver pipeline-diario.yml).
    Motivo de existir a par de 1a: os sentinelas já dispararam por
    ruído confirmado depois (Regulamento da Série II na Issue #114,
    falso positivo do próprio DL 166/2026 na Issue #132) — um rascunho
    "por confirmar" nunca deve ser tratado como pronto, mas também não
    faz sentido perder o sinal só porque ninguém preencheu 1a ainda.
    Deduplicado por OCORRÊNCIA, não por dia: se o mesmo sentinela
    continuar a devolver o mesmo excerto em dias seguintes (já
    aconteceu na prática, ver `SENTINELAS_DIRIGIDOS`/Issue #132), só o
    1.º dia produz rascunho — `data/canal_estado.json` guarda o último
    excerto já rascunhado por sentinela (`sentinelas_rascunhadas`) e só
    volta a disparar quando o excerto for genuinamente diferente (um
    acto novo, não o mesmo a persistir na pesquisa).

2. CALENDÁRIO DE PAGAMENTOS — UMA mensagem por mês, a partir do
   primeiro dia útil, com as datas do mês inteiro, geradas de
   data/calendario_pagamentos.json (fonte já verificada por
   scripts/atualizar_calendario.py / scripts/scraper_calendario.py).
   Nunca um aviso por cada dia de pagamento. "Dia útil" é simplificado
   a segunda-sexta (sem calendário de feriados portugueses — o
   repositório não tem um noutro lado nenhum; documentado aqui como
   limitação conhecida, nunca escondida). Produz sempre `confirmado: true`
   — é informação já verificada, sem julgamento humano por fazer.

Regra de volume: no máximo 1 rascunho/dia, qualquer que seja a origem.
Prioridade fixa: 1a (fila manual, já confirmada) > 1b (sentinela, por
confirmar) > 2 (calendário). Se mais do que um tiver algo pendente no
mesmo dia, os de prioridade mais baixa ficam em espera — nunca são
descartados (`calendario_devido()` continua a devolver o mês enquanto
não for entregue; um sentinela por confirmar continua a re-detectar o
mesmo excerto todos os dias até ser rascunhado), por isso a corrida
seguinte sem nada de prioridade mais alta entrega-os.

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
import re
import sys
from pathlib import Path
from typing import Optional

RAIZ_MODULO = Path(__file__).resolve().parent.parent
SAIDA_OMISSAO = Path("/tmp/canal_rascunho_hoje.json")

DOMINIO = "https://tensdireito.com"

sys.path.insert(0, str(RAIZ_MODULO / "scripts"))
from atualizar_calendario import MESES_PT, PRESTACOES  # noqa: E402

# Os 5 sentinelas dirigidos que já geram Issue própria em
# pipeline-diario.yml (labels "verificar"/"fonte-alterada") — mesma
# chave de aviso escrita em data/scraped/avisos.log por
# scripts/scraper_playwright.py (`_registar_aviso`, chamada com
# `chave_aviso` a partir de `_detectar_decreto_psu`/
# `_detectar_decreto_lei_generico`/`_detectar_portaria_generico`).
# Ordem = a mesma dos blocos de Issue no workflow; só usada para
# desempate determinístico se mais do que um disparar no mesmo dia
# (nunca aleatório — nunca dois rascunhos no mesmo dia de qualquer
# forma, ver regra de volume acima).
SENTINELAS_DIRIGIDOS = {
    "dre_psu_decreto_detectado": "Decreto-Lei sobre a Prestação Social Única (PSU)",
    "dre_habitacao_paer_decreto_detectado": (
        "Decreto-Lei sobre o Apoio Extraordinário à Renda (PAER)"
    ),
    "dre_habitacao_garantia_decreto_detectado": (
        "Decreto-Lei que cita a Garantia Pública no crédito habitação"
    ),
    "dre_ias_portaria_detectada": "Portaria do Indexante dos Apoios Sociais (IAS)",
    "dre_psu_regulamentacao_portaria_detectada": (
        "Portaria que regulamenta o Decreto-Lei da PSU"
    ),
}


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


def avisos_de_hoje(caminho_avisos_log: Path, hoje_iso: str) -> list[str]:
    """
    Linhas de data/scraped/avisos.log datadas de hoje — mesmo filtro do
    step "Abrir Issues se mudanças detectadas" em pipeline-diario.yml
    (`avisos_txt.split('\\n').filter(l => l.startsWith(hoje))`),
    reproduzido aqui para nunca divergir. O ficheiro é cumulativo e
    nunca rotacionado — sem este filtro, uma linha de dias/semanas
    atrás reapareceria como "detectada hoje" para sempre (mesmo bug já
    corrigido nas Issues #55-#58 do MEGA).
    """
    if not caminho_avisos_log.exists():
        return []
    texto = caminho_avisos_log.read_text(encoding="utf-8")
    return [linha for linha in texto.split("\n") if linha.startswith(hoje_iso)]


def obter_deteccao_sentinela(
    avisos_hoje: list[str], ja_rascunhados: dict
) -> tuple[str, str] | None:
    """
    Devolve (chave_aviso, excerto) do primeiro sentinela dirigido com um
    sinal NOVO hoje entre os de `SENTINELAS_DIRIGIDOS` — "novo" quer
    dizer: o excerto detectado hoje é diferente do último excerto para o
    qual este script já preparou um rascunho para essa mesma chave
    (`ja_rascunhados`, vindo de data/canal_estado.json). `None` se
    nenhum sentinela tiver sinal novo hoje.

    Nunca dispara duas vezes para a mesma ocorrência — o mesmo
    decreto-lei/portaria a persistir nos resultados da pesquisa dia
    após dia (já aconteceu na prática: Issue #132, dre_psu a re-detectar
    o próprio DL 166/2026 vários dias seguidos antes de o corte de
    recência ser corrigido). `ja_rascunhados` só regista uma chave
    quando um rascunho foi de facto produzido para ela — se o sinal
    apareceu num dia em que outra origem de maior prioridade ocupou o
    único slot diário, fica por rascunhar e continua elegível no dia
    seguinte (nunca perdido silenciosamente).
    """
    for chave_aviso in SENTINELAS_DIRIGIDOS:
        linha = next((linha for linha in avisos_hoje if chave_aviso in linha), None)
        if linha is None:
            continue
        match = re.search(re.escape(chave_aviso) + r":(.*)$", linha)
        excerto = match.group(1).strip() if match else ""
        if not excerto:
            continue
        if ja_rascunhados.get(chave_aviso) == excerto:
            continue  # mesma ocorrência já rascunhada — nunca repetir
        return chave_aviso, excerto
    return None


def formatar_rascunho_sentinela(chave_aviso: str, excerto: str) -> str:
    nome = SENTINELAS_DIRIGIDOS.get(chave_aviso, chave_aviso)
    linhas = [
        f"[POR CONFIRMAR — {nome}]",
        f"Sinal detectado automaticamente em dre.pt: {excerto}",
        "Confirma o facto na fonte oficial e reescreve este texto em "
        "PT-PT simples antes de sequer pensar em publicar.",
    ]
    return "\n\n".join(linhas)


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
    caminho_avisos_log = raiz / "data" / "scraped" / "avisos.log"

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
            "origem": "fila_manual",
            "confirmado": True,
            "titulo": str(entrada.get("titulo") or "Alteração legal confirmada"),
            "texto": formatar_rascunho_legal(entrada),
            "data": hoje_data.isoformat(),
        }
        estado["ultima_entrega_canal"] = hoje_data.isoformat()
        _guardar_json(caminho_estado, estado)
        _guardar_json(saida, rascunho)
        print(f"Rascunho preparado (alteração legal, confirmada): {rascunho['titulo']}")
        return rascunho

    avisos_hoje = avisos_de_hoje(caminho_avisos_log, hoje_data.isoformat())
    ja_rascunhados = estado.get("sentinelas_rascunhadas", {})
    deteccao = obter_deteccao_sentinela(avisos_hoje, ja_rascunhados)
    if deteccao is not None:
        chave_aviso, excerto = deteccao
        nome = SENTINELAS_DIRIGIDOS[chave_aviso]
        rascunho = {
            "gatilho": "alteracao_legal",
            "origem": "sentinela",
            "confirmado": False,
            "sentinela": chave_aviso,
            # Sem prefixo "Por confirmar —" aqui: o step de Issues do
            # workflow já antepõe "⚠️ Canal (por confirmar)" ao título
            # (rascunho.confirmado === false) — duplicar aqui deixaria o
            # título da Issue com "por confirmar" repetido duas vezes.
            "titulo": nome,
            "texto": formatar_rascunho_sentinela(chave_aviso, excerto),
            "data": hoje_data.isoformat(),
        }
        estado["sentinelas_rascunhadas"] = {**ja_rascunhados, chave_aviso: excerto}
        estado["ultima_entrega_canal"] = hoje_data.isoformat()
        _guardar_json(caminho_estado, estado)
        _guardar_json(saida, rascunho)
        print(f"Rascunho preparado (sentinela, por confirmar): {rascunho['titulo']}")
        return rascunho

    dados_calendario = _carregar_json(caminho_calendario, {})
    mes_dados = calendario_devido(hoje_data, estado, dados_calendario)
    if mes_dados is not None:
        rascunho = {
            "gatilho": "calendario",
            "origem": "calendario",
            "confirmado": True,
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

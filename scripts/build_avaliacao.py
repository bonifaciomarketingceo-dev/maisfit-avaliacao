#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera o bloco de AVALIACOES do dados.json a partir da planilha AO VIVO.

Fluxo (sem IA, sem montagem manual):
  planilha (aba Diario_Avaliacoes) -> linhas -> build_meses() -> validar() -> dados.json

A funcao build_meses() e pura (so recebe linhas) e e a que os testes cobrem.
Nomes de alunos NAO sao lidos nem gravados: so quantidades, perfil, genero e professor.
"""
import datetime
import json
import re

# Colunas da aba Diario_Avaliacoes (indice 0 = coluna A)
C_DATA, C_QTD, C_MAT, C_NOVO, C_H, C_M = 0, 3, 7, 8, 9, 10
C_PROF = {"Lucas": 11, "Edy": 12, "Eduardo": 13, "Luiz": 14, "Maria": 15}
C_CONF = 19  # "OK" / "Verificar" / "Sem detalhe"

NOMES_MES = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
             7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}


def _int(v):
    """Converte celula em inteiro; vazio/texto invalido -> None."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).strip()
    if s == "":
        return None
    try:
        return int(float(s.replace(",", ".")))
    except ValueError:
        return None


def _parse_data(v):
    """Aceita datetime ou texto dd/mm/aaaa. Retorna date ou None."""
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    m = re.match(r"^\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*$", str(v or ""))
    if not m:
        return None
    try:
        return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def build_meses(linhas, promo=None):
    """
    linhas: lista de listas (valores da aba Diario_Avaliacoes, a partir da linha 2).
    Retorna dict {"meses": {...}, "atual": "<n>", "promo": {...}}.

    Regras (handoff secao 2/3):
    - dia sem lancamento = None (nunca 0); meses so existem se tiverem algum lancamento;
    - total do mes = soma das quantidades diarias; detalhe por dia vem das colunas H/M/mat/novo/profs;
    - promocao nao entra no total (vem do arquivo promo, separado).
    """
    meses = {}
    for row in linhas:
        if not row or len(row) <= C_DATA:
            continue
        d = _parse_data(row[C_DATA])
        if d is None:
            continue
        qtd = _int(row[C_QTD]) if len(row) > C_QTD else None
        if qtd is None or qtd == 0:
            # sem lancamento: so entra no mes se houver algum lancamento, ver abaixo
            continue
        m = meses.setdefault(d.month, {
            "nome": NOMES_MES[d.month], "ano": str(d.year), "total": 0, "M": 0, "H": 0,
            "mat": 0, "novo": 0, "profs": {}, "dia": [None] * 31, "det": {}, "temDia": True,
        })
        m["total"] += qtd
        m["dia"][d.day - 1] = qtd
        det = {"q": qtd}
        for chave, col in (("mat", C_MAT), ("novo", C_NOVO), ("H", C_H), ("M", C_M)):
            v = _int(row[col]) if len(row) > col else None
            if v:
                det[chave] = v
                m[chave] = m[chave] + v
        profs = {}
        for nome, col in C_PROF.items():
            v = _int(row[col]) if len(row) > col else None
            if v:
                profs[nome] = v
                m["profs"][nome] = m["profs"].get(nome, 0) + v
        if profs:
            det["profs"] = profs
        m["det"][str(d.day)] = det

    # corta a lista de dias ao tamanho do mes real e remove meses sem total
    saida = {}
    for mnum in sorted(meses):
        m = meses[mnum]
        if m["total"] <= 0:
            continue
        dias_no_mes = _dias_no_mes(int(m["ano"]), mnum)
        m["dia"] = m["dia"][:dias_no_mes]
        saida[str(mnum)] = m
    atual = int(max(saida, key=int)) if saida else None  # numero, igual ao dados.json
    return {"meses": saida, "atual": atual, "promo": promo or {}}


def _dias_no_mes(ano, mes):
    if mes == 12:
        return 31
    return (datetime.date(ano, mes + 1, 1) - datetime.date(ano, mes, 1)).days


def validar(resultado, anterior=None):
    """
    Guardas antes de gravar. Lanca ValueError se algo estiver errado.
    anterior: o dados.json atual (dict) para checar que mes fechado nao mudou.
    """
    meses = resultado["meses"]
    for k, m in meses.items():
        soma_dias = sum(q for q in m["dia"] if q)
        if soma_dias != m["total"]:
            raise ValueError("mes %s: soma dos dias (%d) != total (%d)" % (k, soma_dias, m["total"]))
        soma_det = sum(d["q"] for d in m["det"].values())
        if soma_det != m["total"]:
            raise ValueError("mes %s: soma do detalhe (%d) != total (%d)" % (k, soma_det, m["total"]))
        if m["H"] + m["M"] > m["total"] + 0 and m["H"] + m["M"] != m["total"]:
            # H/M podem ficar vazios em meses sem genero (ex.: junho); so falha se passar do total
            raise ValueError("mes %s: H+M (%d) maior que total (%d)" % (k, m["H"] + m["M"], m["total"]))
    if anterior and "meses" in anterior:
        for k, antigo in anterior["meses"].items():
            if k in meses and antigo.get("total", 0) != meses[k]["total"]:
                # mes fechado so pode mudar se a planilha mudou; aqui so avisamos via erro
                if int(k) != int(resultado.get("atual") or 0):
                    raise ValueError("mes fechado %s mudou de %s para %s"
                                     % (k, antigo.get("total"), meses[k]["total"]))
    return True


def ler_planilha_drive(file_id, sa_key_json):
    """Exporta a planilha AO VIVO como xlsx pelo Drive API e devolve as linhas da aba."""
    import io
    import openpyxl
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload

    creds = service_account.Credentials.from_service_account_info(
        json.loads(sa_key_json), scopes=["https://www.googleapis.com/auth/drive.readonly"])
    svc = build("drive", "v3", credentials=creds, cache_discovery=False)
    req = svc.files().export_media(
        fileId=file_id,
        mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    buf.seek(0)
    wb = openpyxl.load_workbook(buf, data_only=True)
    ws = wb["Diário_Avaliações"] if "Diário_Avaliações" in wb.sheetnames else wb.worksheets[0]
    return [list(r) for r in ws.iter_rows(min_row=2, values_only=True)]


# ---------------------------------------------------------------------------
# Meses congelados (fev-jun): a planilha nao tem o detalhe completo desses meses
# (fev nem tem dias; mar-jun nao tem professores/genero). O painel mostra o que
# esta em meses_fixos.json, copiado do dados.json de 15/11/2026.
# ---------------------------------------------------------------------------
CAMPOS = ("total", "M", "H", "mat", "novo", "profs", "dia", "det", "nome", "ano", "temDia")


def aplicar_fixos(resultado, fixos):
    """Troca os meses congelados pela versao fixa. Avisa se a planilha discordar no total/dias."""
    avisos = []
    meses = resultado["meses"]
    for k, fixo in fixos.items():
        planilha = meses.get(k)
        if planilha is not None:
            if planilha["total"] != fixo["total"]:
                avisos.append("mes %s congelado: planilha total %s, fixo %s"
                              % (k, planilha["total"], fixo["total"]))
            elif fixo.get("dia") and planilha["dia"] != fixo["dia"]:
                avisos.append("mes %s congelado: dias da planilha diferem do fixo" % k)
        meses[k] = fixo
    resultado["meses"] = {k: meses[k] for k in sorted(meses, key=int)}
    resultado["atual"] = int(max(resultado["meses"], key=int)) if resultado["meses"] else None
    return avisos


def comparar(gerado, atual):
    """Compara meses campo a campo. Retorna lista de diferencas (texto simples)."""
    difs = []
    ga, aa = gerado.get("meses", {}), atual.get("meses", {})
    for k in sorted(set(ga) | set(aa), key=int):
        if k not in ga:
            difs.append("mes %s: falta no gerador" % k)
            continue
        if k not in aa:
            difs.append("mes %s: so existe no gerador" % k)
            continue
        for c in CAMPOS:
            va, vg = aa[k].get(c), ga[k].get(c)
            if c == "profs" and isinstance(va, dict):
                # decisao 15/11/2026: professor com zero nao aparece (so visual, numeros iguais)
                va = {n: q for n, q in va.items() if q}
            if vg != va:
                difs.append("mes %s campo %s: atual=%s gerador=%s"
                            % (k, c, json.dumps(aa[k].get(c), ensure_ascii=False)[:120],
                               json.dumps(ga[k].get(c), ensure_ascii=False)[:120]))
    if gerado.get("atual") != atual.get("atual"):
        difs.append("atual: %s x %s" % (atual.get("atual"), gerado.get("atual")))
    if gerado.get("promo") != atual.get("promo"):
        difs.append("promo diferente")
    return difs



# ---------------------------------------------------------------------------
# TRAVA AUTOMATICA DA PLANILHA (handoff 15/11/2026, pedido do Guilherme)
# Se algo estiver estranho, NAO publica e avisa em linguagem simples:
# dia, linha da folha de papel (coluna Q, so leitura) e motivo. Nunca corrige sozinho.
# ---------------------------------------------------------------------------
C_ORIGEM = 16  # coluna Q "Origem na folha" (o codigo so LE, nunca escreve)
MAX_POR_DIA = 8


def _aviso_dia(d, origem, motivo):
    dia = "%02d/%02d" % (d.day, d.month)
    if origem:
        return "Parei a atualização. Dia %s (%s): %s. Confira essa linha na folha." % (dia, origem, motivo)
    return "Parei a atualização. Dia %s: %s. Confira as linhas desse dia na folha." % (dia, motivo)


def conferir_planilha(linhas, publicado=None, hoje=None, meses_congelados=()):
    """Retorna lista de avisos (texto simples). Lista vazia = pode publicar."""
    hoje = hoje or (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=3)).date()
    avisos = []
    for row in linhas:
        if not row or len(row) <= C_DATA:
            continue
        d = _parse_data(row[C_DATA])
        if d is None:
            continue
        origem = ""
        if len(row) > C_ORIGEM and row[C_ORIGEM] not in (None, "", 0):
            origem = str(row[C_ORIGEM]).strip()
        conf = str(row[C_CONF]).strip().lower() if len(row) > C_CONF and row[C_CONF] else ""
        qtd = _int(row[C_QTD]) if len(row) > C_QTD else None
        if conf == "verificar":
            avisos.append(_aviso_dia(d, origem, "a conta não fecha (a conferência da planilha marcou \"Verificar\")"))
        if qtd and d > hoje:
            avisos.append(_aviso_dia(d, origem, "tem avaliação lançada numa data que ainda não chegou"))
        if qtd and qtd > MAX_POR_DIA:
            avisos.append(_aviso_dia(d, origem, "%d avaliações num dia só, mais que o normal (até %d)" % (qtd, MAX_POR_DIA)))
    if publicado:
        novo = build_meses(linhas)["meses"]
        for k, m in novo.items():
            if int(k) in meses_congelados:
                continue
            antes = (publicado.get("meses", {}).get(k) or {}).get("total")
            if antes is not None and m["total"] < antes:
                avisos.append("Parei a atualização. %s: o total caiu de %d para %d. Confira os lançamentos do mês na folha."
                              % (m["nome"], antes, m["total"]))
    return avisos

PLANILHA_ID = "11PaYnqjGvX_roDyeCM0VgbcCKOAn5WaIOMkgOu2D-Nw"


def rodar_sombra(linhas, raiz=".", hoje=None):
    """
    MODO SOMBRA: gera, valida e compara, gravando SO dados_sombra.json e status.json.
    Nunca toca no dados.json publicado.
    """
    import os
    p = lambda n: os.path.join(raiz, n)  # noqa: E731
    atual = json.load(open(p("dados.json"), encoding="utf-8"))
    promo = json.load(open(p("promo.json"), encoding="utf-8"))
    fixos = json.load(open(p("meses_fixos.json"), encoding="utf-8"))
    trava = conferir_planilha(linhas, publicado=atual, hoje=hoje,
                              meses_congelados={int(k) for k in fixos})
    res = build_meses(linhas, promo=promo)
    avisos = aplicar_fixos(res, fixos)
    erro = None
    try:
        validar_saida(res)
    except ValueError as e:
        erro = str(e)
    difs = comparar(res, atual)
    with open(p("dados_sombra.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, separators=(",", ":"))
    ultimo_dia = None
    if res["atual"]:
        m = res["meses"][str(res["atual"])]
        dias = [i + 1 for i, q in enumerate(m["dia"]) if q]
        if dias:
            ultimo_dia = "%02d/%02d" % (dias[-1], int(res["atual"]))
    status = {
        "modo": "sombra",
        "geradoEm": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "avaliacoesAte": ultimo_dia,
        "catracaAte": (atual.get("catracaMeta") or {}).get("atualizadoAte"),
        "bloqueado": bool(trava),
        "avisosTrava": trava,
        "igualAoPublicado": not difs and not erro,
        "diferencas": difs,
        "avisos": avisos,
        "erro": erro,
    }
    with open(p("status.json"), "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=1)
    return status


def validar_saida(res):
    """Validacao que tolera meses congelados sem dias (fev)."""
    for k, m in res["meses"].items():
        dias = [q for q in (m.get("dia") or []) if q]
        if dias and sum(dias) != m["total"]:
            raise ValueError("mes %s: soma dos dias (%d) != total (%d)" % (k, sum(dias), m["total"]))
        det = m.get("det") or {}
        if det and sum(d["q"] for d in det.values()) != m["total"]:
            raise ValueError("mes %s: soma do detalhe != total" % k)
    return True


if __name__ == "__main__":
    import os
    import sys
    chave = os.environ.get("GOOGLE_SA_KEY", "").strip()
    if not chave:
        sys.exit("GOOGLE_SA_KEY ausente")
    st = rodar_sombra(ler_planilha_drive(PLANILHA_ID, chave))
    print(json.dumps(st, ensure_ascii=False, indent=1))

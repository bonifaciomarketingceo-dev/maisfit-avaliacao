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
    atual = max(saida, key=lambda k: int(k)) if saida else None
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
                if k != resultado.get("atual"):
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

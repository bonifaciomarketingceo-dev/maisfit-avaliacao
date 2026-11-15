# -*- coding: utf-8 -*-
"""Testes do gerador de avaliacoes (scripts/build_avaliacao.py).

Os numeros de referencia vem do handoff (secao 4). Sem nomes de alunos aqui:
so quantidades, perfil (R/N), genero (M/H) e professor.
"""
import json
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import build_avaliacao as ba  # noqa: E402


def linha(data, qtd=None, mat=None, novo=None, H=None, M=None, lucas=None, edy=None):
    """Monta uma linha no formato da aba Diario_Avaliacoes (colunas A..T)."""
    r = [data, "", "", qtd, 50, "", "", mat, novo, H, M, lucas, edy, "", "", "", "", "", "", "OK"]
    return r


# Novembro (dias com lancamento), extraido da planilha ao vivo
NOV = [
    linha("03/11/2026", 1, 1, None, 1, None, None, 1),
    linha("04/11/2026", 1, None, 1, None, 1, None, 1),
    linha("05/11/2026", 1, None, 1, None, 1, 1, None),
    linha("06/11/2026", 2, None, 2, 1, 1, None, 2),
    linha("07/11/2026", 1, 1, None, None, 1, 1, None),
    linha("10/11/2026", 6, 5, 1, 1, 5, 2, 4),
    linha("11/11/2026", 6, 2, 4, 1, 5, 1, 5),
    linha("12/11/2026", 1, 1, None, 1, None, None, 1),
    linha("13/11/2026", 1, 1, None, None, 1, 1, None),
]

# Outubro: quantidade por dia (dia -> qtd), da planilha ao vivo
OUT_QTD = {1: 2, 5: 3, 7: 2, 8: 4, 13: 4, 14: 3, 15: 3, 16: 1, 19: 4, 20: 7, 21: 2, 22: 5,
           23: 1, 26: 1, 27: 5, 28: 2, 29: 3, 30: 1}


def outubro():
    return [linha("%02d/10/2026" % d, q) for d, q in OUT_QTD.items()]


def test_novembro_bate_com_o_handoff():
    r = ba.build_meses(NOV)
    m = r["meses"]["11"]
    assert m["total"] == 20
    assert m["M"] == 15 and m["H"] == 5
    assert m["mat"] == 11 and m["novo"] == 9
    assert m["profs"] == {"Edy": 14, "Lucas": 6}
    assert r["atual"] == "11"


def test_novembro_dias_null_quando_sem_lancamento():
    m = ba.build_meses(NOV)["meses"]["11"]
    assert m["dia"][0] is None and m["dia"][1] is None
    assert m["dia"][2] == 1 and m["dia"][9] == 6
    assert len(m["dia"]) == 30  # novembro tem 30 dias


def test_outubro_total_53():
    m = ba.build_meses(outubro())["meses"]["10"]
    assert m["total"] == 53


def test_mes_sem_lancamento_nao_existe():
    r = ba.build_meses(NOV)
    assert "12" not in r["meses"] and "10" not in r["meses"]


def test_promocao_fica_fora_do_total():
    promo = {"11": 0, "9": 2}
    r = ba.build_meses(NOV, promo=promo)
    assert r["meses"]["11"]["total"] == 20
    assert r["promo"] == promo


def test_linha_sem_data_valida_e_ignorada():
    r = ba.build_meses([["xx", "", "", 5]] + NOV)
    assert r["meses"]["11"]["total"] == 20


def test_validar_aceita_resultado_correto():
    r = ba.build_meses(NOV)
    assert ba.validar(r) is True


def test_validar_recusa_soma_errada():
    r = ba.build_meses(NOV)
    r["meses"]["11"]["total"] = 21
    with pytest.raises(ValueError):
        ba.validar(r)


def test_validar_recusa_mes_fechado_que_mudou():
    anterior = {"meses": {"10": {"total": 50}}}
    r = ba.build_meses(outubro() + [linha("01/11/2026", 1)])
    r["atual"] = "11"
    with pytest.raises(ValueError):
        ba.validar(r, anterior)


def test_dados_json_do_repo_mantem_novembro_20():
    """Guarda de regressao: o dados.json commitado nao pode perder os numeros do handoff."""
    caminho = os.path.join(ROOT, "dados.json")
    with open(caminho, encoding="utf-8") as f:
        d = json.load(f)
    nov = d["meses"]["11"]
    assert nov["total"] == 20
    assert sum(q for q in nov["dia"] if q) == 20
    assert d["atual"] == "11" or int(d["atual"]) >= 11

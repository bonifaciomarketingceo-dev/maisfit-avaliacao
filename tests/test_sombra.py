# -*- coding: utf-8 -*-
"""Modo sombra com a copia real da planilha (15/11/2026): tem que sair igual ao dados.json."""
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_avaliacao as ba  # noqa: E402

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "planilha_2026-11-15.txt")


def linhas_fixture():
    out = []
    for l in open(FIXTURE, encoding="utf-8"):
        if l.startswith("#") or not l.strip():
            continue
        p = l.split()
        v = [int(x) for x in p[1:]] + [0] * 10
        out.append([p[0] + "/2026", "", "", v[0], 50, "", ""] + v[1:11] + ["", "", "", "OK"])
    return out


def preparar(tmp_path):
    for n in ("dados.json", "promo.json", "meses_fixos.json"):
        shutil.copy(os.path.join(ROOT, n), tmp_path / n)
    return str(tmp_path)


def test_sombra_nao_mexe_no_dados_json(tmp_path):
    raiz = preparar(tmp_path)
    antes = open(os.path.join(raiz, "dados.json"), encoding="utf-8").read()
    ba.rodar_sombra(linhas_fixture(), raiz)
    assert open(os.path.join(raiz, "dados.json"), encoding="utf-8").read() == antes
    assert os.path.exists(os.path.join(raiz, "dados_sombra.json"))
    assert os.path.exists(os.path.join(raiz, "status.json"))


def test_sombra_fev_a_nov_iguais_exceto_setembro_edy_zero(tmp_path):
    st = ba.rodar_sombra(linhas_fixture(), preparar(tmp_path))
    assert st["erro"] is None
    assert st["avisos"] == []
    # unica diferenca conhecida: setembro tem "Edy": 0 no dados.json (gerador omite zeros)
    assert len(st["diferencas"]) == 1 and st["diferencas"][0].startswith("mes 9 campo profs")
    assert st["avaliacoesAte"] == "13/11"
    assert st["catracaAte"] == "13/11"


def test_totais_de_referencia(tmp_path):
    ba.rodar_sombra(linhas_fixture(), preparar(tmp_path))
    s = json.load(open(tmp_path / "dados_sombra.json", encoding="utf-8"))
    tot = {k: m["total"] for k, m in s["meses"].items()}
    assert tot == {"2": 29, "3": 49, "4": 50, "5": 36, "6": 43, "7": 27, "8": 45,
                   "9": 33, "10": 53, "11": 20}


def test_catraca_de_referencia_intacta():
    d = json.load(open(os.path.join(ROOT, "dados.json"), encoding="utf-8"))
    assert d["catraca"]["13"]["uni"] == 237
    meta = d["catracaMeta"]
    assert meta["unicosMes"] == 589 and meta["atualizadoAte"] == "13/11"
    assert meta["sumindo"] == [534, 41, 144]
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    assert '"unicosMes":662,"atualizadoAte":"31/10"' in html

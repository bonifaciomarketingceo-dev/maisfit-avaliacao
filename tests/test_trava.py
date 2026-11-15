# -*- coding: utf-8 -*-
"""Trava automatica: se a planilha estiver estranha, nao publica e avisa em linguagem simples."""
import datetime
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_avaliacao as ba  # noqa: E402

HOJE = datetime.date(2026, 11, 15)


def linha(data, qtd, conf="OK", origem=""):
    r = [data, "", "", qtd, 50, "", "", None, None, None, None, None, None, "", "", "", origem, "", "", conf]
    return r


def test_planilha_normal_nao_trava():
    assert ba.conferir_planilha([linha("12/11/2026", 1), linha("13/11/2026", 1)], hoje=HOJE) == []


def test_verificar_trava_com_dia_e_linha_da_folha():
    av = ba.conferir_planilha([linha("12/11/2026", 1, "Verificar", "folha de novembro, pág 1, linha 17")], hoje=HOJE)
    assert len(av) == 1
    assert "Dia 12/11" in av[0] and "folha de novembro, pág 1, linha 17" in av[0]
    assert "planilha" not in av[0].split("(")[0]  # nada de "linha 281 da planilha"


def test_sem_coluna_q_avisa_so_dia_e_motivo():
    av = ba.conferir_planilha([linha("12/11/2026", 1, "Verificar")], hoje=HOJE)
    assert "Dia 12/11:" in av[0] and "Confira as linhas desse dia" in av[0]


def test_data_no_futuro_trava():
    assert ba.conferir_planilha([linha("20/11/2026", 1)], hoje=HOJE)


def test_mais_de_8_por_dia_trava():
    assert ba.conferir_planilha([linha("12/11/2026", 9)], hoje=HOJE)
    assert ba.conferir_planilha([linha("12/11/2026", 8)], hoje=HOJE) == []


def test_mes_que_cai_trava():
    publicado = {"meses": {"11": {"total": 20}}}
    av = ba.conferir_planilha([linha("12/11/2026", 1)], publicado=publicado, hoje=HOJE)
    assert any("caiu de 20 para 1" in a for a in av)


def test_aviso_nao_tem_nome_de_aluno():
    av = ba.conferir_planilha([linha("12/11/2026", 1, "Verificar", "folha de novembro, pág 1")], hoje=HOJE)
    assert all(isinstance(a, str) for a in av)


def test_sombra_registra_bloqueio_no_status(tmp_path):
    import shutil
    for n in ("dados.json", "promo.json", "meses_fixos.json"):
        shutil.copy(os.path.join(ROOT, n), tmp_path / n)
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    import test_sombra as ts
    ls = ts.linhas_fixture()
    ls.append(linha("12/11/2026", 1, "Verificar"))
    st = ba.rodar_sombra(ls, str(tmp_path), hoje=HOJE)
    assert st["bloqueado"] is True and st["avisosTrava"]


def test_planilha_real_de_15_11_nao_trava(tmp_path):
    import shutil
    for n in ("dados.json", "promo.json", "meses_fixos.json"):
        shutil.copy(os.path.join(ROOT, n), tmp_path / n)
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    import test_sombra as ts
    st = ba.rodar_sombra(ts.linhas_fixture(), str(tmp_path), hoje=HOJE)
    assert st["bloqueado"] is False and st["avisosTrava"] == []

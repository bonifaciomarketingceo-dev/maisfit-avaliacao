#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robo do painel do Supermercado Cristal (Mais Fit).
Baixa o cristal.json mais recente da pasta PAINEL do Google Drive
e grava em ./cristal/dados.json (o Cloudflare publica sozinho).
Independente do robo do painel de avaliacoes: se falhar, nao afeta nada.
"""
import os, io, json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

PASTA_PAINEL = "102uAcp3wDATXU01a1bvKk14ctk9uJoNM"   # PAINEL - Dados e Programacao
NOME = "cristal.json"
DESTINO = os.path.join("cristal", "dados.json")


def main():
    info = json.loads(os.environ["GOOGLE_SA_KEY"])
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/drive.readonly"])
    svc = build("drive", "v3", credentials=creds, cache_discovery=False)
    q = "'%s' in parents and name='%s' and trashed=false" % (PASTA_PAINEL, NOME)
    files = svc.files().list(q=q, orderBy="modifiedTime desc", pageSize=5,
                             fields="files(id,modifiedTime)", supportsAllDrives=True,
                             includeItemsFromAllDrives=True).execute().get("files", [])
    if not files:
        print("[cristal] Nenhum cristal.json no Drive. Mantendo o do repo.")
        return
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, svc.files().get_media(fileId=files[0]["id"]))
    done = False
    while not done:
        _, done = dl.next_chunk()
    dados = json.loads(buf.getvalue().decode("utf-8"))
    if not isinstance(dados.get("compras"), list) or "meta" not in dados:
        raise SystemExit("[cristal] cristal.json invalido (sem meta/compras).")
    os.makedirs("cristal", exist_ok=True)
    with open(DESTINO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    print("[cristal] %d compras, atualizado em %s." % (len(dados["compras"]), dados["meta"].get("atualizadoEm")))


if __name__ == "__main__":
    main()

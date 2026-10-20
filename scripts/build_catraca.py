#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_catraca.py  (Mais Fit)
Le os relatorios de ACESSOS da catraca na pasta ENTRADA do Drive (Excel ou PDF),
monta os dados da catraca (por dia) e injeta as chaves "catraca" e "catracaMeta"
no dados.json do repositorio (que o robo da avaliacao ja gerou).

Roda no GitHub Actions depois do publish.yml. Usa a mesma conta de servico (GOOGLE_SA_KEY).
NAO mexe na avaliacao: so acrescenta as chaves da catraca no dados.json.

Modo teste local:  python3 build_catraca.py --local <pasta_com_relatorios> [dados.json]
"""
import os, sys, io, re, json, datetime

ENTRADA_FOLDER_ID = "1WDVNwprb6h9z_WhxhtGXFG6JlTJySiw9"  # pasta ENTRADA (mesma da avaliacao)
MES = 10            # Outubro (o painel atual é de Outubro)
ANO = 2026
DADOS_PATH = "dados.json"

SEED = json.loads(r"""{"seed":{"1":{"rot":"01/10/2026 &middot; Quinta-feira","uni":307,"pass":713,"med":"2,3","pico":"19h","perfil":[["Plano não informado na catraca",255],["Plano Família",26],["Autorizado (Xeú)",15],["Anual/Recorrente",6],["Ex-Cross",5]],"horas":{"5":45,"6":44,"7":59,"8":57,"9":61,"10":26,"11":35,"12":22,"13":16,"14":19,"15":31,"16":44,"17":52,"18":58,"19":75,"20":53,"21":16,"22":0,"23":0}},"2":{"rot":"02/10/2026 &middot; Sexta-feira","uni":269,"pass":631,"med":"2,3","pico":"18h","perfil":[["Plano não informado na catraca",222],["Plano Família",21],["Anual/Recorrente",12],["Autorizado (Xeú)",9],["Ex-Cross",5]],"horas":{"5":47,"6":51,"7":62,"8":43,"9":43,"10":19,"11":39,"12":21,"13":19,"14":14,"15":26,"16":36,"17":55,"18":68,"19":45,"20":33,"21":10,"22":0,"23":0}},"3":{"rot":"03/10/2026 &middot; Sábado","uni":81,"pass":190,"med":"2,3","pico":"11h","perfil":[["Plano não informado na catraca",64],["Autorizado (Xeú)",6],["Anual/Recorrente",5],["Plano Família",4],["Ex-Cross",2]],"horas":{"5":0,"6":1,"7":10,"8":30,"9":41,"10":49,"11":56,"12":0,"13":0,"14":0,"15":0,"16":0,"17":1,"18":2,"19":0,"20":0,"21":0,"22":0,"23":0}},"4":{"rot":"04/10/2026 &middot; Domingo","uni":50,"pass":94,"med":"1,9","pico":"10h","perfil":[["Plano não informado na catraca",40],["Autorizado (Xeú)",6],["Plano Família",2],["Anual/Recorrente",2]],"horas":{"5":0,"6":1,"7":0,"8":16,"9":24,"10":32,"11":21,"12":0,"13":0,"14":0,"15":0,"16":0,"17":0,"18":0,"19":0,"20":0,"21":0,"22":0,"23":0}},"5":{"rot":"05/10/2026 &middot; Segunda-feira","uni":328,"pass":770,"med":"2,3","pico":"18h","perfil":[["Plano não informado na catraca",279],["Plano Família",20],["Anual/Recorrente",11],["Autorizado (Xeú)",10],["Ex-Cross",8]],"horas":{"5":38,"6":37,"7":55,"8":36,"9":38,"10":37,"11":35,"12":42,"13":26,"14":23,"15":43,"16":39,"17":68,"18":86,"19":73,"20":63,"21":31,"22":0,"23":0}},"6":{"rot":"06/10/2026 &middot; Terça-feira","uni":346,"pass":790,"med":"2,3","pico":"18h","perfil":[["Plano não informado na catraca",289],["Plano Família",28],["Autorizado (Xeú)",15],["Ex-Cross",7],["Anual/Recorrente",7]],"horas":{"5":51,"6":73,"7":60,"8":49,"9":39,"10":19,"11":39,"12":31,"13":18,"14":21,"15":41,"16":40,"17":70,"18":96,"19":70,"20":42,"21":31,"22":0,"23":0}},"7":{"rot":"07/10/2026 &middot; Quarta-feira","uni":323,"pass":791,"med":"2,4","pico":"18h","perfil":[["Plano não informado na catraca",267],["Plano Família",27],["Autorizado (Xeú)",12],["Anual/Recorrente",10],["Ex-Cross",7]],"horas":{"5":50,"6":50,"7":64,"8":42,"9":53,"10":31,"11":34,"12":26,"13":29,"14":40,"15":51,"16":46,"17":62,"18":73,"19":57,"20":68,"21":15,"22":0,"23":0}},"8":{"rot":"08/10/2026 &middot; Quinta-feira","uni":313,"pass":716,"med":"2,3","pico":"18h","perfil":[["Plano não informado na catraca",260],["Plano Família",24],["Autorizado (Xeú)",12],["Anual/Recorrente",9],["Ex-Cross",8]],"horas":{"5":43,"6":50,"7":63,"8":38,"9":39,"10":40,"11":41,"12":35,"13":30,"14":17,"15":47,"16":41,"17":57,"18":64,"19":47,"20":41,"21":23,"22":0,"23":0}},"9":{"rot":"09/10/2026 &middot; Sexta-feira","uni":239,"pass":517,"med":"2,2","pico":"17h","perfil":[["Plano não informado na catraca",194],["Plano Família",15],["Autorizado (Xeú)",15],["Anual/Recorrente",9],["Ex-Cross",6]],"horas":{"5":32,"6":41,"7":55,"8":51,"9":24,"10":28,"11":25,"12":21,"13":11,"14":12,"15":20,"16":43,"17":57,"18":42,"19":32,"20":20,"21":3,"22":0,"23":0}},"10":{"rot":"10/10/2026 &middot; Sábado","uni":4,"pass":19,"med":"4,8","pico":"6h","perfil":[["Aluno regular",3],["Funcionário/IF",1]],"horas":{"5":1,"6":6,"7":0,"8":0,"9":0,"10":0,"11":2,"12":5,"13":3,"14":0,"15":0,"16":0,"17":2,"18":0,"19":0,"20":0,"21":0,"22":0,"23":0},"incompleto":true},"11":{"rot":"11/10/2026 &middot; Domingo","uni":49,"pass":144,"med":"2,9","pico":"10h","perfil":[["Plano não informado na catraca",38],["Plano Família",7],["Autorizado (Xeú)",3],["Ex-Cross",1]],"horas":{"5":0,"6":0,"7":0,"8":42,"9":30,"10":43,"11":27,"12":2,"13":0,"14":0,"15":0,"16":0,"17":0,"18":0,"19":0,"20":0,"21":0,"22":0,"23":0}},"12":{"rot":"12/10/2026 &middot; Segunda-feira","uni":133,"pass":305,"med":"2,3","pico":"9h","perfil":[["Plano não informado na catraca",106],["Autorizado (Xeú)",12],["Plano Família",10],["Anual/Recorrente",4],["Ex-Cross",1]],"horas":{"5":0,"6":0,"7":6,"8":69,"9":86,"10":73,"11":55,"12":14,"13":2,"14":0,"15":0,"16":0,"17":0,"18":0,"19":0,"20":0,"21":0,"22":0,"23":0}},"13":{"rot":"13/10/2026 &middot; Terça-feira","uni":344,"pass":850,"med":"2,5","pico":"18h","perfil":[["Plano não informado na catraca",285],["Plano Família",23],["Autorizado (Xeú)",15],["Ex-Cross",11],["Anual/Recorrente",10]],"horas":{"5":54,"6":55,"7":62,"8":42,"9":42,"10":23,"11":47,"12":30,"13":22,"14":20,"15":40,"16":44,"17":72,"18":115,"19":71,"20":85,"21":26,"22":0,"23":0}}},"meta":{"p585":584,"sumindo":[511,47,151],"sumindoStatus":"estimativa"}}""")
SEED_0113 = SEED["seed"]      # dias 1..13 (estimativa) + dia 10 livre
CATMETA   = SEED["meta"]      # p585, sumindo, sumindoStatus

WD = ["Segunda-feira","Terça-feira","Quarta-feira","Quinta-feira","Sexta-feira","Sábado","Domingo"]

# ---------- parsing de um relatorio (Excel ou PDF) ----------
def parse_excel_bytes(data):
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    per = []
    for ws in wb.worksheets:
        of=None; ts=[]
        for r in ws.iter_rows(values_only=True):
            a = r[0] if r else None
            h = r[1] if r and len(r)>1 else None
            if isinstance(a,str):
                m = re.search(r'total\s*:?\s*(\d+)\s*alunos', a, re.I)
                if m: of = int(m.group(1))
            if isinstance(h, datetime.datetime): ts.append(h)
        per.append((of, ts))
    with_total = [p for p in per if p[0] is not None]
    if with_total: return with_total[0]
    return max(per, key=lambda p: len(p[1]), default=(None,[]))

def parse_pdf_bytes(data):
    oficial=None; times=[]
    text=""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for pg in pdf.pages:
                text += (pg.extract_text() or "") + "\n"
    except Exception:
        text = ""
    m = re.search(r'total\s*(?:de)?\s*alunos\s*:?\s*(\d+)', text, re.I)
    if m: oficial = int(m.group(1))
    for mt in re.finditer(r'(\d{1,2})[:h](\d{2})', text):
        hh=int(mt.group(1))
        if 0<=hh<=23: times.append(datetime.datetime(2000,1,1,hh,int(mt.group(2))))
    return oficial, times

def parse_report(name, data):
    low = name.lower()
    if low.endswith(".pdf"): return parse_pdf_bytes(data)
    return parse_excel_bytes(data)

def build_day_entry(date, oficial, times):
    horas = {str(h):0 for h in range(5,24)}
    for t in times:
        if 5<=t.hour<=23: horas[str(t.hour)] += 1
    pico = max(range(5,23), key=lambda h: horas[str(h)]) if times else 0
    passg = len(times)
    med = round(passg/oficial,1) if oficial else 0
    rot = "%02d/%02d/%d &middot; %s" % (date.day, date.month, date.year, WD[date.weekday()])
    return {"rot":rot,"uni":oficial,"pass":passg,"med":str(med).replace('.',','),
            "pico":"%dh"%pico,"perfil":[],"horas":horas,"oficial":True}

def is_catraca_report(name):
    n = name.lower()
    return ("acesso" in n and "catraca" in n) or ("relatorio de acessos" in n)

def fn_day(name):
    # pula relatorio de PERIODO: "(01 a 13-10)" / "01 a 13"
    if re.search(r'\d+\s*a\s*\d+', name): return None
    m = re.search(r'\((\d{1,2})-(\d{1,2})\)', name)     # (DD-MM)
    if m and int(m.group(2)) == MES: return int(m.group(1))
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', name)      # YYYY-MM-DD
    if m and int(m.group(2)) == MES: return int(m.group(3))
    return None

# ---------- montar o bloco catraca ----------
def build_catraca(reports):   # reports: list of (name, bytes)
    cat = dict(SEED_0113)      # dias 1..13
    for name, data in reports:
        if not is_catraca_report(name): 
            continue
        oficial, times = parse_report(name, data)
        if oficial is None:
            continue
        dts = sorted(set(t.date() for t in times if t.year == ANO))
        if len(dts) > 1:
            continue                 # relatorio de PERIODO (ex.: 01 a 13) -> a base cobre
        if len(dts) == 1:
            d = dts[0]
        else:
            day = fn_day(name)       # PDF: data vem do nome do arquivo
            if day is None:
                continue
            d = datetime.date(ANO, MES, day)
        if d.month != MES:
            continue
        cat[str(d.day)] = build_day_entry(d, oficial, times)
    # flip estimativa -> oficial quando houver >=15 dias oficiais
    oficiais = sum(1 for v in cat.values() if v.get("oficial"))
    meta = dict(CATMETA)
    if oficiais >= 15:
        meta["sumindoStatus"] = "oficial"
    return cat, meta

# ---------- Google Drive ----------
def drive_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    info = json.loads(os.environ["GOOGLE_SA_KEY"])
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/drive.readonly"])
    return build("drive","v3",credentials=creds,cache_discovery=False)

def list_entrada(svc):
    from googleapiclient.http import MediaIoBaseDownload
    out=[]; page=None
    while True:
        resp = svc.files().list(
            q="'%s' in parents and trashed=false" % ENTRADA_FOLDER_ID,
            fields="nextPageToken, files(id,name,mimeType)",
            pageSize=200, pageToken=page).execute()
        for f in resp.get("files",[]):
            if not is_catraca_report(f["name"]): 
                continue
            fh=io.BytesIO()
            dl=MediaIoBaseDownload(fh, svc.files().get_media(fileId=f["id"]))
            done=False
            while not done: _,done = dl.next_chunk()
            out.append((f["name"], fh.getvalue()))
        page=resp.get("nextPageToken")
        if not page: break
    return out

def main():
    if len(sys.argv)>=3 and sys.argv[1]=="--local":
        folder=sys.argv[2]
        dados_path = sys.argv[3] if len(sys.argv)>3 else None
        reports=[]
        for fn in os.listdir(folder):
            p=os.path.join(folder,fn)
            if os.path.isfile(p):
                reports.append((fn, open(p,"rb").read()))
    else:
        svc=drive_service()
        reports=list_entrada(svc)
        dados_path=DADOS_PATH

    cat, meta = build_catraca(reports)

    if dados_path and os.path.exists(dados_path):
        dados=json.load(open(dados_path, encoding="utf-8"))
        dados["catraca"]=cat
        dados["catracaMeta"]=meta
        json.dump(dados, open(dados_path,"w",encoding="utf-8"),
                  ensure_ascii=False, separators=(",",":"))
        print("dados.json atualizado com catraca: %d dias, status=%s" %
              (len(cat), meta["sumindoStatus"]))
    else:
        # modo teste sem dados.json: so mostra o resumo
        dias=sorted(cat.keys(), key=int)
        print("catraca dias:", dias)
        for d in dias:
            print("  dia %s: uni=%s pass=%s oficial=%s" %
                  (d, cat[d]["uni"], cat[d]["pass"], cat[d].get("oficial",False)))
        print("catracaMeta:", meta)

if __name__ == "__main__":
    main()

# Painel Mais Fit — Avaliações Físicas

Painel do domínio **painel.bonifaciomkt.com.br** (site Netlify `maisfit-avaliacoes`).

## Como funciona
- `index.html` — o painel. Ele lê os números do arquivo `dados.json` (mesma pasta).
- `dados.json` — os dados (total do mês, gênero, perfil, professores, dia a dia, promoção).
- `.github/workflows/publish.yml` — o **robô**. Todo dia útil ele:
  1. baixa o `dados.json` novo da pasta **PAINEL - Dados e Programação** do Google Drive;
  2. grava esse `dados.json` aqui no repositório (o Netlify republica o painel sozinho);
  3. remonta a planilha mestre (Excel) a partir de `modelo_planilha.xlsx` + `dados.json` e
     grava de volta na pasta **2026** do Drive (mesmo arquivo).
- `scripts/fetch_and_build.py` — o código que faz o item acima.
- `modelo_planilha.xlsx` — o modelo (template) da planilha mestre, com abas, fórmulas e gráficos.

## Segredo necessário (uma vez)
No GitHub: **Settings → Secrets and variables → Actions → New repository secret**
- Nome: `GOOGLE_SA_KEY`
- Valor: todo o conteúdo do arquivo `.json` da conta de serviço `robo-painel`.

A conta `robo-painel@maisfit-painel.iam.gserviceaccount.com` precisa ter acesso **Editor**
à pasta **Avaliações** do Drive.

## Testar na hora
Aba **Actions → Publicar painel Mais Fit → Run workflow**.

# Painel Mais Fit — guia para o Claude Code

## Arquitetura
- Repo público -> Cloudflare Pages -> painel.bonifaciomkt.com.br (`index.html` lê `dados.json`).
- `publish.yml` (seg–sex 17:10 UTC): `scripts/fetch_and_build.py` baixa o `dados.json` do Drive e remonta a planilha mestre.
- `catraca.yml` (seg–sex 17:45 UTC): `scripts/build_catraca.py` injeta catraca/catracaMeta/catracaHist.
- `build_avaliacao.py`: gera o bloco de avaliações a partir da planilha AO VIVO (`build_meses`, `validar`). Ainda NÃO ligado ao publish.yml — ligar só depois de validar com a planilha real.
- `cristal.yml` / `cristal/`: outro painel. NÃO mexer.

## Regras de negócio (não mudar sem o Guilherme pedir)
- Meta 50/mês. Professor R$10 por avaliação paga. R$50 = 1; R$100 = 2 (duas pessoas na linha).
- Linha "Promoção" não soma no total (`promo.json`).
- Dia sem lançamento = null (nunca 0).
- Gênero pelo nome; perfil R = renovação, N = novo.
- Nome de aluno NUNCA no repo, painel, dados.json ou aviso. Nomes só no CSV privado do Drive.
- Catraca: pessoas únicas = total oficial do rodapé. Autorizados ("Aut. Xeu", "Aut. Cros") CONTAM. Fora: "func" e shell/Marcelo Xeu.
- Virada de mês automática; mês fechado não muda.
- Professor com zero avaliações no mês NÃO aparece na lista do mês (decisão 15/11/2026; só visual, totais e pagamento iguais). Aplicado pelo gerador.
- Fev–Jun ficam congelados em `meses_fixos.json` (a planilha não tem professores/gênero desses meses).
- Gerador em MODO SOMBRA: grava `dados_sombra.json` e `status.json`, não publica. Ligar à publicação só com aprovação do Guilherme.

## Trava automática da planilha (pedido do Guilherme, 15/11/2026)
- Antes de publicar o gerador confere a planilha: dia com "Verificar" na coluna T, data no futuro, mais de 8 avaliações num dia, ou total de mês menor que o já publicado => NÃO publica e avisa.
- O aviso diz em linguagem simples o DIA, a linha da FOLHA DE PAPEL (coluna Q "Origem na folha", só leitura; o código nunca escreve nela) e o MOTIVO. Nunca "linha N da planilha". Sem coluna Q: só dia e motivo.
- Não corrige sozinho. Sem leitura dupla da folha (decisão do Guilherme).
- Hoje roda só em modo sombra: resultado em `status.json` (`bloqueado`, `avisosTrava`).

## Números de referência (teste de regressão, 15/11/2026)
- Avaliação: Out 53, Nov 20 (15 M / 5 H · 11 R / 9 N · Edy 14 / Lucas 6).
- Catraca: Nov 589 únicas até 13/11; Out 662 até 31/10; sumindo [534, 41, 144].

## Como rodar e testar
- `python -m pip install pytest openpyxl` depois `python -m pytest -q tests`
- O workflow `test.yml` roda em todo push/PR. Os robôs só commitam com testes verdes.

## NUNCA
- Colocar nome de aluno no repo/painel.
- Mexer no Cristal.
- Apagar histórico de meses.
- Commitar sem testes verdes.
- Mudar regra de negócio sem pedido.

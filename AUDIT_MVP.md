# BuscaLeilão — auditoria de eventos e links (P0.3/P0.4)

**Início:** 04/11/2026. **Fonte de verdade:** `app/events.json` publicado na coleta #41816001753 (47 eventos únicos, 98 registros, 19 UFs). Nenhum candidato PNCP/RSS equivale a evento publicado.

**Critério de conclusão:** revisar 20 eventos distintos, de fontes/UFs variados, confirmando explicitamente data, UF, organizador, veículos, fonte oficial ou leiloeiro legítimo e utilidade do destino. Não basta o coletor automatizado ter passado. Links para agendas genéricas devem estar identificados e ser úteis. Qualquer inconsistência exige correção e nova verificação.

| # | Evento ID | Origem/UF | Situação da auditoria | Observação |
|---|---|---|---|---|
| 1 | `curitiba-smdt-16-2026` | Prefeitura de Curitiba/PR | **Conferência de edital e link aprovada** | Catálogo municipal confirma edital 16/2026, sucatas inservíveis, 11/11 9h; link leva ao catálogo oficial, não à página individual |
| 2 | `curitiba-smdt-17-2026` | Prefeitura de Curitiba/PR | **Conferência de edital e link aprovada** | Edital 17/2026, veículos em circulação, 11/11 9h; catálogo oficial |
| 3 | `curitiba-smdt-18-2026` | Prefeitura de Curitiba/PR | **Conferência de edital e link aprovada** | Edital 18/2026, veículos em circulação, 25/11 9h; catálogo oficial |
| 4 | `vieiras-001-2026` | Prefeitura de Vieiras/MG | **Conferência de edital e link aprovada** | Aviso municipal confirma 13/11 13h, veículos entre os bens; link oficial da notícia |
| 5 | `serranopolis-iguacu-pr-01-2026` | Prefeitura de Serranópolis do Iguaçu/PR | **Conferência de edital e link aprovada** | Prefeitura confirma 12/11 8h30 e veículos; link oficial da notícia |
| 6 | `detran-go-03-2026-11-09` | DETRAN Goiás/GO | **Conferência oficial aprovada** | Portal Detran confirma 09/11 às 9h, edital 03/2026 e 656 carros + 1.533 motos = 2.189 veículos |
| 7 | `detran-ba-23-2026` | DETRAN Bahia/BA | **Conferência oficial aprovada** | Portal Detran-BA: edital 23/2026, 25/11 às 9h, Salvador/Alagoinhas/Santo Antônio de Jesus; fonte é edital específico |
| 8 | `mogi-2026-11-06` | Prefeitura de Mogi das Cruzes/SP | **Conferência oficial aprovada** | Notícia oficial confirma 84 veículos, 06/11 às 10h, leilão online; URL de notícia específica e não portal de lances |
| 9 | `lorena-2026-11-10` | Prefeitura de Lorena/SP | **Conferência oficial aprovada** | Aviso municipal confirma fechamento em 10/11 às 10h, 63 lotes de veículos/sucatas; site da Destak é mencionado como plataforma, mas o link no feed é notícia oficial |
| 10 | `fernando-prestes-03-2026` | Prefeitura de Fernando Prestes/SP | **Conferência oficial aprovada** | Edital 03/2026 confirma 05/11 às 9h, leilão presencial de veículos e outros bens na sede municipal |
| 11 | `cuiaba-semob-4-2026-11-11` | Prefeitura de Cuiabá/MT | **Conferência oficial aprovada** | Aviso confirma quarta sessão em 11/11 às 9h para lotes não arrematados; total geral de 1.065 não é contagem da sessão |
| 12 | `prf-es-2026-11-04` | PRF/ES | **Conferência oficial aprovada** | PRF confirma 3ª sessão em 04/11 às 10h, edital 2/2026, veículos e sucatas; link oficial do edital |
| 13 | `freitas-8158-2026-11-06` | Freitas/SP | **Conferência do leiloeiro aprovada** | Página individual 8158 mostra veículos e lotes em 06/11 às 10h; calendário confirma Pátio Utinga |
| 14 | `freitas-8162-2026-11-09` | Freitas/SP | **Conferência do leiloeiro aprovada** | Página individual 8162 confirma fechamento 09/11 às 10h, online, local São Paulo/SP; visitação de alguns lotes no RJ não altera UF do evento |
| 15 | `copart-10569-2026-11-04` | Copart/GO | **Conferência da plataforma aprovada** | Página individual /saleListResult/10569/2026-11-04 mostra lista de venda Goiânia-GO, data 04/11 e lotes; URL não é calendário genérico |
| 16 | `copart-10570-2026-11-04` | Copart/GO | **Parcial — evento corroborado, link pendente** | Resultado indexado da própria Copart mostra venda 10570 em Goiânia, 04/11, leiloeiro Ygor Ferreira Brasil; destino exato do feed não abriu no teste externo. Não considerar usabilidade do link aprovada |
| 17 | `copart-10573-2026-11-05` | Copart/CE | **Parcial — data/local corroborados, ID/link pendentes** | Calendário oficial Copart confirma Eusébio-CE em 05/11, mas não comprova venda individual 10573 nem sua abertura |
| 18 | `copart-10586-2026-11-10` | Copart/PR | **Pendente — link individual** | A página do ID 10586 não abriu; calendário indexado consultado não confirmou independentemente a venda de 10/11. Não substituir automaticamente por inventário geral de Curitiba |
| 19 | `vip-2026-11-07-0900-2eb73e64869302-pr` | VIP Leilões/PR | **Parcial — evento identificado; acesso pendente** | A própria VIP indexa edital 071126PINHAISPR e página de evento https://www.vipleiloes.com.br/evento/detalhes/071126pinhaispr, com 07/11 09h, PR, 26 lotes. Acesso direto redirecionou em loop no verificador; feed aponta para agenda, não para esse evento |
| 20 | `vip-2026-11-14-0900-18c4f200a245a5-pe` | VIP Leilões/PE | **Parcial — evento identificado; acesso pendente** | A própria VIP indexa edital 141126CTTUPE e página de evento https://www.vipleiloes.com.br/evento/detalhes/141126cttupe, com 14/11 09h, PE, 13 lotes. Acesso direto redirecionou em loop no verificador; feed aponta para agenda |

## Ampliação controlada da amostra — eventos já presentes no feed (04/11/2026)

Os cinco links originais problemáticos não são aprovados por substituição silenciosa: permanecem documentados na tabela principal. Para cumprir **pelo menos 20 eventos distintos com links úteis**, a auditoria pode incorporar outros eventos já publicados, desde que cada um passe pelo mesmo critério.

| # | Evento ID | Origem/UF | Situação | Evidência e destino |
|---|---|---|---|---|
| 21 | `cuiaba-semob-4-2026-11-04` | Cuiabá/MT | **Conferência oficial aprovada** | Notícia municipal acessível confirma a sessão de 04/11 às 9h, lotes 359 a 715; URL específica do evento |
| 22 | `cuiaba-semob-4-2026-11-05` | Cuiabá/MT | **Conferência oficial aprovada** | Mesma notícia confirma a sessão independente de 05/11 às 9h, lotes 716 a 999; não confundir com a sessão de 04/11 |
| 23 | `prf-sp-2026-11-04` | PRF São Paulo/SP | **Conferência oficial aprovada** | Edital nº 01/2026 acessível no portal PRF, confirma 03 e 04/11 às 10h, veículos conservados e sucatas; URL oficial |
| 24 | `freitas-8152-2026-11-04` | Freitas/SP | **Parcial** | Resultado público indexado identifica leilão 8152, 04/11 às 10h em Santa Bárbara d'Oeste; acesso direto ao destino retornou HTTP 403 no verificador, portanto não contar como link aprovado |

Fontes independentes: [Cuiabá — cronograma por sessão](https://www.cuiaba.mt.gov.br/noticias/semob-realiza-o-4o-leilao-do-ano-com-1-065-veiculos-disponiveis), [PRF/SP — edital 01/2026](https://www.gov.br/prf/pt-br/assuntos/leiloes-prf/sao-paulo/sp-edital-de-leilao-de-veiculos-conservados-e-sucatas-1), [Freitas 8152 — acesso ao leilão](https://www.freitasleiloeiro.com.br/Leiloes/Lotes?leilaoId=8152).

**Progresso: 18 eventos distintos com documentação e destino acessível / meta de 20.** Permanecem cinco links originais não aprovados e um candidato adicional com bloqueio HTTP 403. O resultado do mecanismo de pesquisa, sozinho, não comprova navegação real.

## Evidências externas verificadas nesta rodada

- [DETRAN Goiás — comunicado oficial com 2.189 veículos e início às 9h](https://goias.gov.br/detran/detran-go-realiza-leilao-de-veiculos-de-mais-de-2-mil-veiculos/)
- [DETRAN Bahia — edital específico nº 23/2026](https://www.ba.gov.br/detran/editais/7742/edital-de-leilao-no-232026-veiculos-conservados-e-sucatas-aproveitaveis)
- [Mogi das Cruzes — notícia oficial de 84 veículos, 06/11 às 10h](https://site.mogidascruzes.sp.gov.br/noticia/no-dia-6-de-novembro-prefeitura-fara-leilao-online-para-venda-de-84-veiculos?imprimir=1)
- [Lorena — aviso oficial sobre encerramento 10/11 às 10h](https://www.lorena.sp.gov.br/wordpress/index.php/2026/10/22/prefeitura-de-lorena-realiza-leilao-de-veiculos-inserviveis-e-sucatas/)
- [Fernando Prestes — edital 03/2026, 05/11 às 9h](https://www.fernandoprestes.sp.gov.br/portal/editais/0/1/2638)
- [Cuiabá — quatro sessões da Semob e sessão de não arrematados em 11/11](https://www.cuiaba.mt.gov.br/noticias/semob-realiza-o-4o-leilao-do-ano-com-1-065-veiculos-disponiveis)
- [PRF Espírito Santo — edital 2/2026 com terceira sessão em 04/11](https://www.gov.br/prf/pt-br/assuntos/leiloes-prf/espirito-santo/edital-de-licitacao-no-2-2026-egvr-es)
- [Freitas — leilão 8158 de 06/11, lotes de veículos](https://www.freitasleiloeiro.com.br/Leiloes/Lotes?leilaoId=8158)
- [Freitas — leilão 8162 de 09/11, fechamento às 10h](https://www.freitasleiloeiro.com.br/Leiloes/Lotes?leilaoId=8162)
- [Copart — lista de venda 10569 Goiânia em 04/11](https://www.copart.com.br/saleListResult/10569/2026-11-04?location=Goi%C3%A2nia%20-%20GO&saleDate=1793793600000)


- [Catálogo de leilões de Curitiba — editais 16, 17 e 18/2026](https://transito.curitiba.pr.gov.br/patio/leilao-eletronico-de-veiculos/52)
- [Leilão de Vieiras — aviso municipal](https://vieiras.mg.gov.br/noticias/prefeitura-de-vieiras-realizara-leilao-eletronico-de-bens-moveis-no-dia-13-de-novembro-de-2026)
- [Leilão de Serranópolis do Iguaçu — aviso municipal](https://serranopolis.pr.gov.br/noticias/6113-governo-municipal-de-serranopolis-do-iguacu-realiza-leilao-eletronico-de-veiculos-maquinas-e-outros-bens)
- [Editais DETRAN Goiás](https://goias.gov.br/detran/leiloes/) — referência parcial para nº 03/2026.

**Progresso auditado até aqui:** **18 eventos distintos totalmente conferidos / meta de 20** após ampliação controlada da amostra (15 originais + 3 adicionais). **Cinco links originais permanecem pendentes** (3 Copart, 2 VIP), além de Freitas 8152 bloqueado no acesso independente. A aprovação documental de links oficiais não equivale a teste real em todos os navegadores. A verificação de acesso aos sites por diferentes usuários/navegadores ainda precisa de teste de produto. Não marcar P0.3/P0.4 como concluídos.

## Segunda rodada — checagem das cinco pendências (04/11/2026)

A validação independente identificou **três eventos anteriormente pendentes com evidência adicional de existência**, mas não resolveu a usabilidade dos respectivos destinos:

- **Copart 10570/GO:** resultado da plataforma identifica venda, local e data; o URL exato do feed segue sem confirmação de abertura independente.
- **Copart 10573/CE:** calendário oficial confirma data/local do leilão; o ID de venda específico ainda precisa ser validado.
- **Copart 10586/PR:** somente a origem de coleta automatizada informa venda; não promover sem acesso e evidência independente.
- **VIP PR 07/11:** página individual identificada por busca pública em `/evento/detalhes/071126pinhaispr`; data, UF e natureza veicular constatadas no conteúdo indexado. Redirecionamento em loop impede validar a navegação ao vivo.
- **VIP PE 14/11:** página individual identificada por busca pública em `/evento/detalhes/141126cttupe`; data, UF e lotes de veículos constatados no conteúdo indexado. Redirecionamento em loop impede validar a navegação ao vivo.

Fontes da checagem: [Copart 10570 indexado](https://www.copart.com.br/saleListResult/auctionId/10570?auctioneer=Ygor+Ferreira+Brasil+-+Juceg+074%2F20%3Fpage%3D3&from=&liveAuction=false&location=Goi%C3%A2nia+-+GO&saleDate=1793808000000&yardNum=56), [calendário Copart](https://www.copart.com.br/salesListResult), [VIP PR](https://www.vipleiloes.com.br/evento/detalhes/071126pinhaispr), [VIP PE](https://www.vipleiloes.com.br/evento/detalhes/141126cttupe), [agenda VIP indexada na página principal](https://www.vipleiloes.com.br/).

**Status formal permanece 15/20 completos:** links que falham ao abrir ou não conduzem ao evento não atendem P0.4. Dois eventos VIP e dois Copart têm corroboração parcial; um Copart continua sem conferência independente. Não substituir por URLs supostas ou declarar P0.3/P0.4 completos.

**Correção de código:** `scripts/validate_feed.py` passa a recusar `source_link_type=event` com URL de calendário, data Copart divergente ou link de domínio não reconhecido. Testes verificam Copart/VIP, sem alterar a agenda pública nem forçar links inacessíveis.

## Próxima ação

Concluir pelo menos mais dois eventos distintos com links efetivamente acessíveis, mantendo os cinco links originais problemáticos na lista de riscos do produto. Validar Copart/VIP em navegador real antes de alterar os links publicados. Só fechar P0.3/P0.4 quando houver pelo menos 20 aprovados e uma decisão explícita sobre os links genéricos da VIP.

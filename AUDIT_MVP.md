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
| 16 | `copart-10570-2026-11-04` | Copart/GO | **Pendente** | URL tem ID de venda 10570 distinto de 10569, mas página específica não abriu na verificação externa; não contar como comprovada |
| 17 | `copart-10573-2026-11-05` | Copart/CE | **Pendente** | URL da venda 10573 não acessível na verificação externa; conferir página específica |
| 18 | `copart-10586-2026-11-10` | Copart/PR | **Pendente** | URL da venda 10586 não acessível na verificação externa; conferir página específica |
| 19 | `vip-2026-11-07-0900-2eb73e64869302-pr` | VIP Leilões/PR | **Pendente** | Agenda VIP em loop de redirecionamento na consulta externa; link é calendário, não evento; necessita teste real de navegação |
| 20 | `vip-2026-11-14-0900-18c4f200a245a5-pe` | VIP Leilões/PE | **Pendente** | Agenda VIP em loop de redirecionamento na consulta externa; data/UF exigem verificação humana e teste do link |

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

**Progresso auditado até aqui:** **15/20 conferidos** quanto a data/UF/organizador e utilidade da fonte; **5 pendentes** (3 links Copart não acessíveis na verificação externa, 2 eventos VIP com agenda em loop). A aprovação documental de links oficiais não equivale a teste real em todos os navegadores. A verificação de acesso aos sites por diferentes usuários/navegadores ainda precisa de teste de produto. Não marcar P0.3/P0.4 como concluídos.

## Próxima ação

Resolver as cinco verificações restantes (3 Copart e 2 VIP) por acesso direto/navegador real, sem inferir de URLs a confirmação independente. Depois corrigir o que for comprovadamente inconsistente e iniciar P0.5.

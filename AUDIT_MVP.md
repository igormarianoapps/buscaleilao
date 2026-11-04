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
| 6 | `detran-go-03-2026-11-09` | DETRAN Goiás/GO | **Parcial** | Portal oficial confirma leilão 03/2026 em 09/11, mas concluir confronto completo da quantidade e hora |
| 7 | `detran-ba-23-2026` | DETRAN Bahia/BA | Pendente | Conferir edital, horário e destino |
| 8 | `mogi-2026-11-06` | Prefeitura de Mogi das Cruzes/SP | Pendente | Conferir 84 veículos, data e horário |
| 9 | `lorena-2026-11-10` | Prefeitura de Lorena/SP | Pendente | Confirmar 10/11 e link |
| 10 | `fernando-prestes-03-2026` | Prefeitura de Fernando Prestes/SP | Pendente | Conferir edital e hora |
| 11 | `cuiaba-semob-4-2026-11-11` | Prefeitura de Cuiabá/MT | Pendente | Conferir sessão própria e horário |
| 12 | `prf-es-2026-11-04` | PRF/ES | Pendente | Conferir sessão e link |
| 13 | `freitas-8158-2026-11-06` | Freitas/SP | Pendente | Conferir data, pátio e acesso a leilão específico |
| 14 | `freitas-8162-2026-11-09` | Freitas/SP | Pendente | Conferir data, pátio e acesso a leilão específico |
| 15 | `copart-10569-2026-11-04` | Copart/GO | Pendente | Validar venda específica e URL |
| 16 | `copart-10570-2026-11-04` | Copart/GO | Pendente | Venda distinta no mesmo pátio/dia; validar URL |
| 17 | `copart-10573-2026-11-05` | Copart/CE | Pendente | Validar venda e URL |
| 18 | `copart-10586-2026-11-10` | Copart/PR | Pendente | Validar venda e URL |
| 19 | `vip-2026-11-07-0900-2eb73e64869302-pr` | VIP Leilões/PR | Pendente | Conferir data/UF no calendário; destino é agenda, não evento |
| 20 | `vip-2026-11-14-0900-18c4f200a245a5-pe` | VIP Leilões/PE | Pendente | Conferir data/UF no calendário; destino é agenda, não evento |

## Evidências externas verificadas nesta rodada

- [Catálogo de leilões de Curitiba — editais 16, 17 e 18/2026](https://transito.curitiba.pr.gov.br/patio/leilao-eletronico-de-veiculos/52)
- [Leilão de Vieiras — aviso municipal](https://vieiras.mg.gov.br/noticias/prefeitura-de-vieiras-realizara-leilao-eletronico-de-bens-moveis-no-dia-13-de-novembro-de-2026)
- [Leilão de Serranópolis do Iguaçu — aviso municipal](https://serranopolis.pr.gov.br/noticias/6113-governo-municipal-de-serranopolis-do-iguacu-realiza-leilao-eletronico-de-veiculos-maquinas-e-outros-bens)
- [Editais DETRAN Goiás](https://goias.gov.br/detran/leiloes/) — referência parcial para nº 03/2026.

**Progresso auditado até aqui:** 5/20 concluídos quanto a data/UF/organizador e utilidade da fonte; 1 parcial; 14 pendentes. A verificação de acesso aos sites por diferentes usuários/navegadores ainda precisa de teste de produto. Não marcar P0.3/P0.4 como concluídos.

## Próxima ação

Continuar a inspeção individual das 15 linhas ainda não concluídas, priorizando sites de leiloeiros, datas/horas e links específicos versus agendas. Corrigir registros inseguros ou incorretos e repetir a coleta. Depois iniciar P0.5.

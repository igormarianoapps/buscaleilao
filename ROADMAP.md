# BuscaLeilão — checklist do projeto

## Ciclo de desenvolvimento — 11/11/2026 (branch develop, sem deploy)

- [x] Criada branch `develop` a partir de `main`; `main` permanece intacta pelas mudanças deste ciclo.
- [x] Previews automáticos desabilitados no projeto Vercel `buscaleilao` para evitar consumo de deploys durante os commits.
- [x] Filtros por palavra-chave (título, cidade, organizador e identificador), combinados com UF e intervalo; busca tolerante a acentos.
- [x] Link público exige página específica de lotes; avisos oficiais e editais são evidência, não destino de clique.
- [x] Coleta passa por duas camadas de aprovação: identificação da rota exata e política de evento/organizador/domínio; itens não aprovados vão para quarentena.
- [x] Casos de teste para falso domínio, HTTPS enganoso, página de notícia, rota genérica, associação incorreta e busca.
- [ ] Confirmar execução verde do CI e nova coleta de desenvolvimento sem escrever no feed da `main`.
- [ ] Auditar ao vivo uma amostra diversificada de destinos, status e redirecionamentos. Conferência estrutural não substitui checagem de leiloeiro habilitado nem garante ausência de fraude.
- [ ] Gerar `app/index.html` com feed validado em desenvolvimento, testar desktop e mobile.
- [ ] Aprovação do usuário para merge em `main` e um único deploy posterior.

**Exemplo Semob:** aviso municipal e destino individual `https://www.focoleiloes.com.br/leilao/497/lotes`. A sessão de 11/11 às 10h não deve ser apresentada como nova oportunidade após seu encerramento.

---


Atualizado em 04/11/2026. **Implementado** significa código publicado no GitHub; execução e cobertura reais dependem do próximo relatório.

## Marco do MVP — critérios de lançamento

**Produto:** agenda nacional de **eventos de leilão de veículos**, não catálogo de lotes. Público consegue filtrar por UF e data e consultar a fonte. O produto não promete listar todos os leilões do Brasil.

**Estado em 03/11/2026:** pré-MVP funcional. Três coletas completas consecutivas aprovadas: #41715100215 (03/11, 48 eventos), #41814063834 (04/11, 44 eventos) e #41816001753 (04/11, 47 eventos únicos, 98 registros, 19 UFs, 18/21 fontes curadas verificadas). **P0.1, P0.2 e P0.6 concluídos.** Auditoria P0.3/P0.4 é a próxima fase.

### P0 — Bloqueadores para lançamento público

- [x] **P0.1 — Uma execução ponta a ponta** do workflow atual deve passar por testes, Copart, VIP/Freitas, PNCP, fila de revisão e publicação. Conferir todos os arquivos produzidos e logs, especialmente `app/pncp-candidates.json` e `app/vip-dom-diagnostics.json` (quando houver fallback).
- [x] **P0.2 — Estabilidade:** observar 3 coletas completas consecutivas com sucesso do workflow e feed atualizado dentro de 24h; a falha de uma fonte não pode bloquear o feed. Registrar taxa de fontes recuperadas e motivos de falha.
- [ ] **P0.3 — Qualidade dos eventos:** auditar manualmente pelo menos 20 eventos de organizadores e UFs variados; 100% devem ter data futura verificável, UF correta, organizador claro e URL de origem segura. Deduplicação por evento; não inventar hora/veículos.
- [ ] **P0.4 — Links úteis:** links individuais quando comprovados; onde houver apenas agenda, rotular como agenda e testar se o destino é útil. Não tratar endereço genérico como link do evento.
- [ ] **P0.5 — Auditoria da experiência:** desktop/mobile, filtros, timezone de Brasília, estados sem resultados, aviso de feed antigo, links externos, acessibilidade básica e ausência de falhas de interface.
- [x] **P0.6 — Confiabilidade de publicação (código e testes):** o feed verificado é validado e publicado antes de PNCP/RSS; falhas da descoberta não bloqueiam o feed. **Validação ponta a ponta aprovada na execução #41715100215.**
- [ ] **P0.7 — Lançamento controlado:** testar com 5–10 pessoas e registrar erros de evento, buscas sem resultado, links quebrados e compreensão da proposta antes de abrir divulgação ampla.

### P1 — Melhorias após o MVP inicial

- [ ] Extrair links individuais da VIP quando tecnicamente confirmados (agenda funciona como fallback rotulado).
- [ ] Ampliar leiloeiros pequenos, municipais e novas UFs usando PNCP e editais validados.
- [ ] Automatizar conferência de adiamentos/cancelamentos quando o edital permitir.
- [ ] Aumentar cobertura por UF e organizador com metas baseadas em dados observados; nunca prometer exaustividade.
- [ ] Evoluir triagem de candidatos em cadastros curados auditáveis.

### Fora do escopo do MVP

- Catálogo de lotes e veículos individuais, login, alertas, estimativas de preços, lances, compras e garantia de cobertura de todos os leilões.

### Ordem recomendada

1. **Estabilizar coleta/CI (P0.1, P0.2 e P0.6)**, sem acrescentar novos coletores até cumprir os critérios.
2. **Auditar qualidade/links (P0.3, P0.4)** e corrigir erros objetivos.
3. **Testar produto ponta a ponta (P0.5)** em desktop e mobile.
4. **Piloto com usuários (P0.7)** e decisão de lançamento baseada nos critérios, não em quantidade arbitrária de fontes.

**Definição de pronto:** todos os P0 acima concluídos. P1 não bloqueia o MVP.

## Execução P0 — Etapa 1: estabilização do MVP (03/11/2026)

- [x] Separar publicação do feed validado das tarefas experimentais PNCP/RSS, publicando primeiro `events.json`, `collection-report.json` e `source-health.json`.
- [x] Tornar diagnóstico, RSS, PNCP e priorização não bloqueantes; guardar seus relatórios em commit separado, apenas quando os arquivos existem.
- [x] Criar `scripts/validate_feed.py` para impedir publicação de feed vazio, eventos vencidos, UFs inválidas, links não HTTPS, IDs duplicados e divergência entre feed e relatório.
- [x] Adicionar testes automatizados do gate e da ordem do workflow de publicação; testes GitHub Actions aprovados.
- [x] Executar testes quando `.github/workflows/collect.yml` mudar.
- [x] **P0.1:** coleta completa validada na execução #41715100215, incluindo PNCP, revisão, publicação e resumo.
- [ ] **P0.2:** 2/3 coletas completas consecutivas bem-sucedidas; falta uma execução posterior com sucesso e feed atualizado dentro de 24h.
- [ ] Em seguida iniciar auditoria de eventos/links (P0.3/P0.4); não iniciar novos coletores antes disso.

**Referência permanente:** a sequência de entrega do MVP continua P0.1/P0.2/P0.6 → P0.3/P0.4 → P0.5 → P0.7. Novas funcionalidades ficam em P1.

## Execução P0.1 — diagnóstico por workflow (03/11/2026)

- [x] Criar `scripts/mvp_run_summary.py`: resumo do GitHub Actions com contagem de eventos, UFs, fontes aprovadas/com falha, links diretos, PNCP, fila de revisão e diagnóstico VIP.
- [x] Distinguir arquivos gerados na coleta atual de relatórios antigos (janela de 35 minutos); **dados antigos não contam como nova validação**.
- [x] Executar resumo mesmo quando houver falha, para facilitar investigação do P0.1.
- [x] Testes de atualização e antiguidade do relatório aprovados no GitHub Actions: execução **41714263734**.
- [x] **P0.1:** execução completa de `Collect verified auctions` confirmada (#41715100215), todas as etapas concluídas com sucesso.
- [ ] **P0.2:** 1/3 coletas completas consecutivas aprovadas (#41715100215). Contar apenas workflow completo, não testes isolados.
- [ ] Verificar após a próxima coleta a recuperação de Aracaju/Curitiba e a geração de candidatos PNCP, sem transformá-los automaticamente em eventos.

**Regra operacional:** continuar apenas com P0.1/P0.2 antes de iniciar P0.3/P0.4, mantendo o checklist MVP como fonte de verdade.

## Execução P0.1 — proteção contra dados antigos (03/11/2026)

- [x] Impedir que a fila de revisão reaproveite PNCP/RSS de uma coleta anterior após erro nas etapas experimentais. São admitidos apenas arquivos com `checked_at` recente (até 6h).
- [x] Acrescentar `rss_fresh` e `pncp_fresh` ao resumo da fila para identificar se a pesquisa foi atualizada.
- [x] Impedir que o resumo operacional de uma execução falha trate um `collection-report.json` antigo como evidência nova para P0.1/P0.2.
- [x] Testar descarte de pesquisa antiga e relatório de feed antigo; suíte no GitHub Actions.
- [x] **P0.1:** execução ponta a ponta confirmada (#41715100215); todos os passos concluídos e arquivos publicados.
- [ ] **P0.2:** 1/3 execuções completas consecutivas (#41715100215); testes de adaptadores não contam.

**Prioridade mantida:** não adicionar fontes ou funcionalidades até validar o pipeline completo (P0.1/P0.2); então auditar eventos/links (P0.3/P0.4).

## P0.1 validado — execução completa de 03/11/2026, 17h43 BRT

- [x] Workflow **41715100215** concluído com sucesso, incluindo testes, coleta, validação de integridade, publicação do feed, RSS, PNCP, fila de revisão e resumo operacional.
- [x] **48 eventos únicos**, 111 registros por UF, **19/27 UFs**, Copart 12 eventos, VIP 16, Freitas 3, Curitiba 3.
- [x] **19 de 22 fontes curadas** verificadas; bloqueadas: Aracaju (403), Pedranópolis (403), Superbid (403).
- [x] VIP: **24 cartões DOM**, modo `complete_cards`, 79 registros por estado. Sem diagnóstico de erro porque não houve fallback. Links individuais ainda não confirmados.
- [x] PNCP: **25 candidatos** em `app/pncp-candidates.json`, sem publicação automática; fila de revisão 105 pistas (25 PNCP + 80 RSS).
- [x] Dados publicados com sucesso. P0.1 passa; **P0.2 = 1/3**, aguardando duas coletas completas posteriores.
- [x] Ajustar após análise os pedidos PNCP para **não insistir após HTTP 429** (4 erros de limite registrados na primeira coleta; alterações submetidas a testes automatizados).
- [ ] Confirmar segunda e terceira coletas completas e verificar atualização do feed em até 24 horas entre execuções.
- [ ] Após P0.2, seguir para auditoria de eventos e links (P0.3/P0.4), sem adicionar novos coletores.

## P0.2 — Consistência de datas entre coletor e interface (03/11/2026)

- [x] Confirmar na API do GitHub Actions que **a execução #41715100215 permanece como a única coleta completa recente**; P0.2 segue **1/3**, sem contar testes unitários.
- [x] Centralizar a regra de data no fuso `America/Sao_Paulo` com `scripts/auction_clock.py`.
- [x] Alinhar Copart, VIP, Freitas, fontes curadas e gate de integridade do feed à data de Brasília, mantendo horários de auditoria em UTC.
- [x] Criar testes de regressão para 00h30 UTC (ainda dia anterior no Brasil), 03h30 UTC (novo dia no Brasil), datetime sem fuso e validação de eventos na virada; suíte do GitHub Actions **41716845637 aprovada**.
- [ ] P0.2: validar **mais duas coletas completas consecutivas** com o novo código e atualização do feed dentro de 24 horas; resultado atual continua **1/3**.
- [ ] Ao atingir 3/3, iniciar P0.3/P0.4 (auditoria de pelo menos 20 eventos e links).

**Regra:** nenhum novo leiloeiro, expansão de escopo ou funcionalidade P1 antes de concluir a estabilidade.

## P0.2 — Histórico verificável de estabilidade (04/11/2026)

- [x] Conferir GitHub Actions: até a consulta de 04/11 pela manhã ainda não houve **segunda execução completa de `Collect verified auctions`**. P0.2 permanece **1/3**.
- [x] Criar `app/collection-history.json` com ponto inicial **41715100215**, comprovadamente concluído com sucesso: 48 eventos, 19 UFs, verificado em 03/11 às 17h43 BRT.
- [x] Criar `scripts/record_collection_history.py` para registrar após as etapas de coleta/publicação cada `GITHUB_RUN_ID`, tentativa, horário de verificação, eventos únicos, UFs e saúde das fontes.
- [x] Calcular sequência de coletas registradas com distância máxima de 24 horas entre atualizações, reiniciando a sequência quando o intervalo for maior; execuções repetidas da mesma tentativa não duplicam a contagem.
- [x] Manter ressalva explícita: **registro final não equivale a sucesso**; confirmar o estado `conclusion=success` de cada execução no GitHub antes de marcar P0.2.
- [x] Cobrir o histórico com testes de 3 execuções, intervalo maior que 24h, arquivos antigos, ID inválido e ordem do workflow.
- [ ] Verificar segunda e terceira execuções completas. Não contar o workflow `Test auction adapters` para a meta P0.2.

**Próxima etapa após 3/3:** auditoria de fontes/eventos e links P0.3/P0.4; não ampliar escopo antes.

## P0.2 — Segunda coleta validada, recuperação de Curitiba (04/11/2026)

- [x] Execução manual **#41814063834** concluída com `success` em todas as etapas, incluindo publicação e histórico; intervalo dentro de 24h desde a coleta anterior. **P0.2: 2/3**.
- [x] Resultado: **44 eventos únicos, 95 registros, 19 UFs**; **15 fontes curadas aprovadas e 6 falhas**. Contagem diminuiu principalmente por 3 editais de Curitiba indisponíveis na coleta.
- [x] Identificar regressão operacional: os três editais de Curitiba compartilham um catálogo municipal e falharam juntos por `Page.goto: Timeout 15000ms exceeded`. Acessibilidade da fonte varia entre coletas; não manter eventos sem evidência atual.
- [x] Ajustar fallback Chromium **apenas para o domínio oficial de Curitiba**: `wait_until=commit`, timeout de navegação 25s, aguardar DOM e texto visível. Não contornar bloqueios HTTP, HTTPS ou aceitar evidência parcial.
- [x] Testes de página compartilhada garantem uma tentativa de browser por URL e impedem validar edital ausente; workflow **#41814652857 aprovado**.
- [ ] Validar Curitiba na próxima execução completa após a correção e verificar se as demais fontes permanecem estáveis.
- [ ] **P0.2: 2/3** — confirmar uma terceira coleta completa consecutiva dentro de 24h; depois iniciar P0.3/P0.4.

**Ordem do MVP preservada:** estabilização P0.2 → auditoria dos 20 eventos/links P0.3/P0.4 → interface P0.5 → piloto P0.7.

## P0.2 concluído — três execuções verificadas (04/11/2026)

- [x] GitHub Actions: #41715100215, #41814063834 e #41816001753 concluídos com sucesso, em intervalos inferiores a 24 horas.
- [x] Última coleta: 47 eventos únicos, 98 registros, 19 UFs, 18 fontes curadas aprovadas e 3 fontes com HTTP 403.
- [x] Curitiba: três editais novamente verificados; PNCP: 27 candidatos, ainda não publicados.
- [ ] **P0.3/P0.4 — fase atual:** **19/20 eventos distintos com destino e documentação conferidos** (15 originais + duas sessões de Cuiabá + PRF-SP + Campina Grande). Os cinco links originais problemáticos (3 Copart, 2 VIP) continuam abertos e há um evento Freitas 8152 apenas parcialmente confirmado. Não encerrar P0.4 até decisão sobre acessibilidade dos destinos e rótulo dos links.
- [ ] P0.5 — testar interface desktop/mobile após a auditoria.
- [ ] P0.7 — piloto com usuários depois da interface.

## P0.3/P0.4 — Auditoria de links, segunda rodada (04/11/2026)

- [x] Encontrar fontes públicas da Copart e links individuais indexados da VIP para eventos da amostra, preservando o estado parcial quando o destino não abre.
- [x] VIP PR 07/11 09h: edital `071126PINHAISPR`, página `/evento/detalhes/071126pinhaispr`, 26 lotes; acesso em verificador externo apresenta loop.
- [x] VIP PE 14/11 09h: edital `141126CTTUPE`, página `/evento/detalhes/141126cttupe`, 13 lotes; acesso em verificador externo apresenta loop.
- [x] Copart GO 10570 04/11: resultado indexado com venda específica, mas acesso à URL original do feed ainda não validado; CE 10573 confirmado apenas em calendário por data/UF; PR 10586 ainda não corroborado individualmente.
- [x] Endurecer gate de publicação: `source_link_type=event` precisa ser URL individual comprovável pela estrutura oficial (Copart ID + data, VIP rota individual). Proibir rotular calendário como evento. Testes aprovados no workflow **41817984600**.
- [ ] **P0.3/P0.4: 15/20 completas**; cinco links exigem teste de navegação efetiva, sem considerar conteúdo indexado como garantia de acesso.
- [ ] Só avançar à experiência P0.5 depois de resolver as cinco pendências ou substituí-las por outros eventos auditados com links úteis (mantendo amostra variada).

**Detalhamento e evidências:** `AUDIT_MVP.md`. Não inferir cobertura de mercado a partir das 19 UFs.

## P0.3/P0.4 — Amostra ampliada sem aprovação artificial de links (04/11/2026)

- [x] Auditoria chegou a **18 eventos distintos conferidos de 20 necessários**: mais duas sessões Cuiabá/MT (04/11 e 05/11, horários e lotes separados) e PRF-SP (04/11 10h), todos em páginas governamentais acessíveis.
- [x] Validar em fonte pública indexada Copart 10571 (Itaquaquecetuba, 04/11), VIP PR 07/11 e VIP PE 14/11, **sem declarar aprovados links que dão timeout/loop ao abrir**.
- [ ] Manter as cinco pendências iniciais (Copart 10570/10573/10586 e VIP PR/PE) como risco do produto até navegação real confirmada ou alternativa útil comprovada.
- [ ] Freitas 8152: página indexada informa evento, mas abertura pelo verificador externo retorna HTTP 403; ainda não aprovado para P0.4.
- [ ] Auditar mais um evento diferente com URL exata do feed acessível antes de considerar P0.3/P0.4 concluídos.
- [ ] Depois iniciar P0.5 — interface desktop/mobile.

**Evidências e critérios:** `AUDIT_MVP.md`. Não criar fonte nova para compensar falha sem necessidade de produto.

## P0.3/P0.4 — Campina Grande aprovada, links restritos mantidos (04/11/2026)

- [x] Conferir URL exata `https://www.marcotulioleiloes.com.br/leiloes/355`, edital da Prefeitura de Campina Grande/PB e data 04/11 às 10h, com lotes de veículos visíveis.
- [x] Confirmar existência da venda Copart 10577/PE na rota alternativa oficial indexada; **não aprovar a URL exata do feed** sem abertura comprovada.
- [x] Tentar rotas exatas de Copart 10571, 10577 e Freitas 8152: não acessíveis no verificador; nenhuma das três foi marcada como aprovada.
- [ ] Amostra atualmente **19/20** com links exatos acessíveis. Falta **1**; os cinco links originais Copart/VIP continuam no registro de riscos.
- [ ] Não iniciar P0.5 até conclusão ou tratamento explícito das falhas de link P0.4.

## P0.4 — Transparência de links genéricos e checagem do 20º evento (04/11/2026)

- [x] Conferir leilão Freitas 8152/SP em resultado do índice da própria plataforma: 04/11 às 10h, Santa Bárbara d'Oeste, veículos, leiloeiro e edital. **Não contabilizar como aprovado**: acesso direto da URL do feed retorna HTTP 403 na verificação externa.
- [x] Confirmar que `https://www.vipleiloes.com.br/agenda` apresenta loop de redirecionamento na verificação externa; não publicar outra URL sem validação.
- [x] Melhorar `app/index.html`: indicar nos cards de calendário que a pessoa deve localizar data e UF na **agenda geral**, não em um leilão individual; avisar sobre dependência de disponibilidade do site externo.
- [x] Adicionar testes `tests/test_calendar_link_ui.py` de rótulos de calendário, escape de URL e segurança dos links externos.
- [ ] **P0.3/P0.4 seguem 19/20 aprovados**: Freitas 8152 é o candidato mais próximo de completar 20, porém o acesso real ainda está bloqueado; Copart e VIP continuam sob acompanhamento.
- [ ] Validar pelo menos mais um destino realmente acessível e a navegabilidade de calendários VIP antes de encerrar P0.3/P0.4 e iniciar P0.5.

**Registro de evidências e URLs:** `AUDIT_MVP.md`.

## P0.4 bloqueado externamente; pré-revisão técnica P0.5 (04/11/2026)

- [x] Revalidar Freitas 8152 via conteúdo do índice público; a URL exata do feed ainda devolve HTTP 403 no acesso direto, então não somar como 20º evento.
- [x] Revalidar loop de redirecionamento VIP na agenda e em duas páginas individuais; não forçar links novos nem declarar que abrem.
- [x] Corrigir três sequências `\\n` literais em `app/index.html`, que afetavam CSS e HTML dos cartões.
- [x] Adicionar foco visível para navegação por teclado e ajustes responsivos de formulários/cartões em telas até 600px.
- [x] Testes de regressão incluídos em `tests/test_calendar_link_ui.py`; GitHub Actions **#41821699242 concluído com sucesso**.
- [ ] **P0.3/P0.4: 19/20**, aguardando destino 20º acessível e validação de utilidade da VIP.
- [ ] **P0.5: pré-revisão técnica iniciada**, ainda sem verificação funcional visual em navegadores reais.

**Não mudar a definição de pronto:** CSS e testes automatizados não substituem auditoria visual e navegação real.

## P0.5 — Filtros, resultados vazios e estados de erro (04/11/2026)

- [x] Corrigir comportamento de busca que fazia nova requisição HTTP a cada alteração de filtros: `app/index.html` agora carrega o feed apenas uma vez por abertura de página e filtra localmente. O horário de Brasília continua sendo calculado a cada pesquisa.
- [x] Adicionar botão **Limpar filtros** para restaurar UF/data e os resultados da sessão sem nova solicitação à rede.
- [x] Diferenciar mensagens para ausência de eventos verificados, ausência de eventos na UF, na data, ou em ambos os filtros (`emptyResultsMessage` em `app/agenda.mjs`).
- [x] Distinguir erro de carregamento / formato inválido do feed de uma busca legítima sem resultados.
- [x] Garantir estados com `role="status"` e manter os alertas de feed antigo, links em nova aba com `noopener noreferrer` e ordenação de eventos.
- [x] Testes Node + Python cobrem mensagens por filtro, renderização estática, cache de filtro e **sintaxe de JavaScript inline**; GitHub Actions **#41822399945 aprovado** (corrigido erro inicial na expressão regular do teste).
- [ ] **P0.5 continua em andamento**: falta validar comportamento visual e navegação reais em desktop/mobile, com teclado, filtros, ausência de resultados e feed vencido.
- [ ] **P0.3/P0.4 continuam abertos em 19/20** com risco de links externos Copart/VIP, conforme `AUDIT_MVP.md`.
- [ ] Piloto P0.7 somente após resolver critérios pendentes de lançamento.

**Prioridade preservada:** confiabilidade da agenda e uso sem fricção; não criar novos coletores ou funcionalidades P1 durante o fechamento do MVP.

## P0.5 — Lista vazia e pesquisa por período (04/11/2026)

- [x] Usuário relatou página sem resultados mesmo com `app/events.json` contendo **98 registros / 47 eventos únicos** na última coleta #41816001753. O problema é compatível com rotas de assets absolutas erradas para o diretório publicado na Vercel; não presumir ausência de leilões.
- [x] Trocar URLs absolutas `/app/agenda.mjs` e `/app/events.json` pelas relativas `./agenda.mjs` e `./events.json`, válidas quando `app` é a raiz do site ou quando a página é servida de `/app/`.
- [x] Trocar filtro de data única por **intervalo De / Até**, inclusivo, com ambos os campos opcionais e validação `De <= Até`.
- [x] Respeitar a data atual em `America/Sao_Paulo` também em intervalos abertos; não reintroduzir eventos vencidos.
- [x] Atualizar mensagem de pesquisa sem resultados e comportamento do botão Limpar filtros para ambos os campos.
- [x] Testes Node para limites inclusivos, limites opcionais, filtros de UF e intervalo invertido; testes Python verificam URLs relativas, campos e sintaxe do módulo JS. **GitHub Actions #41823401886 aprovado**.
- [ ] **Validar na Vercel** com abertura real em desktop/mobile, incluindo feed, scripts, resultados e filtros. A rota incorreta é causa provável; sem inspeção direta da configuração Vercel não afirmar que o problema de produção está definitivamente solucionado.
- [ ] P0.3/P0.4 continuam 19/20 links comprovados; não bloquear correção da interface por falhas externas VIP/Copart.

**Próximo teste manual:** abrir https://buscaleilao-nine.vercel.app/ após o deploy e conferir lista inicial sem filtros, intervalo de 04/11 a 14/11, UF GO, UF sem registros e erro De > Até.

## P0.5 — Correção crítica: estados vazios e feed não carregado (04/11/2026)

- [x] Reproduzir por análise do código a causa provável: `app/index.html` usava `import ... from "./agenda.mjs"` no topo; se Vercel publica `app/index.html` na raiz mas mantém o repositório como raiz, `/agenda.mjs` falha e **toda a execução do módulo é interrompida**, inclusive a população das 27 UFs.
- [x] Trocar importação estática por importação dinâmica com fallback dos dois layouts possíveis: `/app/agenda.mjs` e `./agenda.mjs`. O seletor de estados é preenchido **antes** da tentativa de carregar o módulo.
- [x] Aplicar a mesma resolução dupla ao feed, `/app/events.json` e `./events.json`, exigindo HTTP OK e objeto JSON com array `events`, sem assumir que HTTP 200 signifique JSON válido.
- [x] Exibir mensagem explícita se módulo e feed não forem encontrados; manter intervalo de datas inclusivo De/Até e filtro de UF.
- [x] Atualizar testes de regressão para os dois layouts, escolha dos estados independente do import e sintaxe JavaScript; **GitHub Actions #41824162450 aprovado**.
- [ ] **Verificação em produção pendente:** confirmar no navegador a lista de UFs e os cartões reais em https://buscaleilao-nine.vercel.app/ após deploy; testes de código não substituem o comportamento da Vercel.
- [ ] Continuar P0.5 e os bloqueios externos de P0.4 em 19/20, sem alterar o escopo.

**Lição do defeito:** não usar importação estática em ponto de entrada cujo caminho depende do diretório publicado; capturar o erro de forma visível.

## P0.5 — Site público recuperado e verificado em Chromium (04/11/2026)

- [x] Diagnóstico confirmado pelo relato do usuário: a página publicada falhava ao carregar `agenda.mjs`/`events.json` via URLs externas e exibia mensagem de erro.
- [x] Publicar página **autossuficiente** em `app/index.html` com dados verificados embutidos (98 registros, 47 leilões únicos) e filtros incorporados do código central `app/agenda.mjs`.
- [x] Criar `scripts/build_static_page.py` para gerar HTML a partir de `app/index.template.html`, `app/agenda.mjs` e `app/events.json`; sem requisições de arquivos na inicialização da página.
- [x] Integrar geração **depois da validação do feed** e publicar `app/index.html` no mesmo commit dos dados; futuras coletas atualizam a página automaticamente.
- [x] Testes de regressão asseguram que HTML gerado corresponde exatamente ao feed, não publica feed vazio, escapa conteúdo perigoso e executa JS válido.
- [x] **Teste funcional em produção:** Chromium abriu https://buscaleilao-nine.vercel.app/ com **HTTP 200**, **28 opções no seletor (27 UFs + Todos)**, **47 cards**, **GO com 4 resultados**, **GO com período 04/11–25/11 com 4**, botão Limpar restaurou **47**, **zero erros JS**. GitHub Actions **#41825376777 concluído com sucesso**.
- [ ] Revisar visualmente uso mobile real e acessibilidade com usuário; P0.5 ainda não finalizado integralmente.
- [ ] P0.3/P0.4 segue **19/20** devido a links externos não comprovados. P0.7 segue pendente.

**Regra:** manter `app/index.template.html` como fonte editável da UI; `app/index.html` é gerado. Mudanças visuais futuras não devem ser feitas apenas no arquivo gerado.

## P0.4 — Links diretos para lotes: VIP e Detran-GO (04/11/2026)

- [x] **Detran-GO 03/2026 (09/11):** localizar página específica da leiloeira [PMKLog](https://pmklog.com.br/leilao/evento/leilao-detran/?evento=fa724af3-d396-11f1-a2f8-02420a000014), com lotes; registrar `event_url` em `app/sources.json` e no feed, preservando o `source_url` da notícia governamental para validação independente. O CTA principal usa `event_url`; link do comunicado fica separado.
- [x] **VIP Leilões:** encontrar o erro real no DOM com Playwright: data/UF ficam em elementos internos, mas o `href` específico está no contêiner externo `.card-evento`. Corrigir o extrator e provar em execução real **#41827763874**: 24 cartões, 15 leilões com links específicos e 68 registros por UF; incluindo `04/11 14h` com GO e URL oficial `/evento/detalhes/041126bsgo`.
- [x] Corrigir `choose_vip_events`: só publicar registros VIP com link individual correspondente ao cartão; não utilizar `/agenda` como destino do usuário. Evitar correlacionar eventos por data isolada; exigir assinatura de data, hora e UFs.
- [x] Atualizar feed já verificado: **14 eventos VIP e 61 registros por UF** tiveram correspondência exata com links diretos; dois grupos permaneceram sem correspondência (06/11 14h com conjunto de UFs divergente; 14/11 09h PE sem cartão capturado) e deixam de aparecer na busca por `source_link_type=calendar` até verificação.
- [x] `app/index.template.html` privilegia URL de lotes para evento com `event_url` e mantém fonte oficial secundária; aviso/edital sem URL de lotes fica rotulado como tal.
- [x] Suíte automatizada aprovada em **#41827977258**; o código e `app/index.html` gerado estão no GitHub.
- [ ] **Deploy bloqueado:** Vercel informou `Deployment rate limited — retry in 24 hours` no status do commit. **Não declarar produção atualizada** até novo deploy bem-sucedido e smoke test em navegador real.
- [ ] Continuar P0.4: conferir individualmente links VIP com páginas que não exibem lotes (a plataforma pode indicar `Em loteamento`) e substituir demais URLs de notícias por páginas de leiloeiros somente com correspondência documental segura.
- [ ] P0.5/P0.7 permanecem pendentes; não iniciar ampla divulgação antes do deploy funcional e da auditoria.

**Princípio de produto:** separar fonte de comprovação de link onde ver veículos; não inventar o destino quando só existe uma agenda pública.

## Fase 1 — Motor de coleta e qualidade

- [x] Coletores independentes: erro de uma fonte não interrompe a verificação das outras
- [x] Verificação paralela limitada para anúncios oficiais
- [x] Uma consulta HTTP por URL: páginas compartilhadas são reaproveitadas
- [x] Preservar evidências de HTML estático e navegador em fontes com múltiplas sessões; teste de regressão incluído
- [x] Fallback Chromium para erro de rede ou texto dinâmico, sem desativar HTTPS nem insistir em HTTP 403/401
- [x] Histórico de saúde por fonte: último sucesso, erro e falhas consecutivas em `app/source-health.json`
- [x] Não publicar anúncio sem as evidências configuradas; não manter como confirmado um evento indisponível
- [x] Testes unitários de isolamento, cache de páginas, erro 403, fallback, cancelamento e evidência compartilhada
- [x] Avisar na interface quando a última coleta passou de 36h ou não tem data confiável
- [x] Exibir tipo de fonte correto: municipal, estadual, federal ou privada
- [x] Executar testes Python no workflow de coleta **antes** de atualizar o feed
- [x] Deduplicação de registros multiestaduais somente com mesmo `event_id`
- [x] Validar arquitetura nova e coletor Freitas na coleta de 03/11/2026, 16h40 BRT: 41 eventos únicos, 19 UFs e 3 leilões Freitas
- [x] Evitar duplicação de eventos com links individuais Freitas/Superbid, mesmo quando os coletores utilizam IDs diferentes (aguarda próxima execução)
- [x] Extrair IDs e URLs de vendas individuais da Copart quando presentes nas células do calendário; distinguir vendas simultâneas no mesmo pátio e dia (aguarda execução)
- [x] Identificar links diretos versus links genéricos do calendário na interface e no relatório (aguarda execução)
- [x] Implementar extração conservadora de cartões VIP: data e UFs devem pertencer ao mesmo cartão, URL HTTPS individual apenas quando única e do domínio VIP (aguarda execução)
- [ ] Confirmar URLs e IDs individuais da VIP: coleta de 17h07 registrou zero cartões DOM, mantendo o calendário
- [x] Ampliar busca de cartões VIP para campos de data e rótulo separados; gerar diagnóstico DOM quando não encontrados (aguarda execução)
- [x] Garantir que leitura parcial de cartões VIP não substitua o calendário completo: comparar todos os eventos por data/hora/UF antes de promover links individuais; testes aprovados, coleta real pendente
- [x] Gravar diagnóstico VIP também para cartões parciais, não apenas quando nenhum cartão é encontrado
- [x] Validar novos testes de cobertura VIP (completa, parcial e ambígua): workflow 41710733146 aprovado em 03/11/2026
- [ ] Confirmar próxima coleta real com detecção de cartões VIP e o novo relatório de diagnóstico, sem perder eventos já verificados
- [x] Respeitar explicitamente bloqueio HTTP 429 sem retry imediato com navegador (aguarda execução)
- [x] Tratar links Copart cuja data aparece como «LIVE NOW», aceitando a data apenas quando consta no URL oficial (aguarda execução)
- [ ] Conferir estabilidade dos novos links Copart na coleta automática
- [ ] Detectar adiamentos e cancelamentos com o edital original
- [ ] Quantidades de veículos apenas quando comprovadas pela fonte

## Fase 2 — Cobertura nacional

- [x] Coleta pública inicial de Copart e VIP
- [x] Fontes oficiais curadas: prefeituras, PRF e Detrans (lista em `app/sources.json`)
- [x] Acrescentar leilões de pequenos municípios: Serranópolis do Iguaçu/PR e Pedranópolis/SP (novos, aguardando execução)
- [x] Descoberta RSS direcionada para UFs em rodízio até percorrer os 27 entes federativos
- [x] Fila de triagem recente em `app/review-queue.json`, sem publicação automática de notícias
- [x] Implementar extração de URL/ID específico da Copart com testes de domínio, data e vendas duplicadas no mesmo pátio
- [x] Adicionar tentativa de extração de URLs individuais da VIP e testes para cartões com links ambíguos ou domínios inválidos (aguarda execução)
- [ ] Medir taxa de links específicos da VIP na coleta real
- [x] Implementar um adaptador independente de calendário da Freitas Leiloeiro, validando data/UF na página individual; aguarda execução real
- [x] Adicionar páginas oficiais específicas da Freitas (dois eventos) e Superbid (um evento), sujeitas à verificação do coletor
- [x] Integrar descoberta nacional oficial via PNCP (leilões eletrônicos modalidade 1 e presenciais 13); candidatos separados da agenda pública
- [x] Validar modalidade, objeto veículo, data futura e UF; não publicar diretamente o prazo de propostas como data confirmada do leilão
- [x] Criar testes de formatos PNCP, rejeição de imóveis/cancelamentos, falhas de API e ambas modalidades (workflow 41711457851 aprovado)
- [x] Melhorar alcance do PNCP com busca por semanas recentes, evitando limite de páginas do período inteiro; aceitar editais sem data apenas na fila de revisão
- [x] Unificar fila de revisão PNCP + RSS, registrando origem de cada pista, sem publicação automática
- [ ] Validar coleta real da API PNCP e converter editais aprovados em eventos públicos
- [ ] Criar adaptadores próprios para outros leiloeiros com calendário público verificável
- [x] Priorizar notícias com data explícita futura no título e excluir notícias com data de leilão comprovadamente passada (triagem, sem publicação automática)
- [x] Testar datas de títulos (28/10/2026; “próximo dia 28”; 12 de novembro de 2026) e manter datas apenas como pistas não verificadas — workflow 41711104446 aprovado
- [ ] Automatizar conversão de notícias em candidaturas com data, UF, documento e URL original validados
- [x] Incluir relatório de UFs sem eventos e percentual de presença, sem confundir isso com cobertura de mercado
- [ ] Medir cobertura de leiloeiros/prefeituras por UF; não confundir presença em UF com cobertura completa
- [x] Identificar catálogo oficial alternativo de Curitiba e substituir fonte bloqueada; acessibilidade automática aguarda coleta

## Entrega de descoberta — 03/11/2026

- [x] Busca PNCP por cinco janelas semanais, nas duas modalidades de leilão (eletrônico/presencial), com paginação limitada e falhas isoladas.
- [x] Editais PNCP sem prazo explícito são pistas de pesquisa com data desconhecida; não aparecem em `app/events.json`.
- [x] `app/review-queue.json` reúne notícias RSS e oportunidades PNCP, identifica origem e mostra contadores separados.
- [x] Evitar repetir candidato PNCP que já conste em `app/sources.json`.
- [ ] Conferir `app/pncp-candidates.json`, `app/vip-dom-diagnostics.json` e contagens após a próxima coleta real.
- [ ] Confirmar editais PNCP individualmente e transformar os comprovados em fontes curadas.

## Melhoria de cobertura — 03/11/2026

- [x] Priorizar editais PNCP dos estados **sem eventos** na última coleta, usando somente a lista real `states_without_events` do relatório.
- [x] Limitar a 10 candidatos PNCP por UF na fila para evitar que estados grandes monopolizem a revisão.
- [x] Identificar `coverage_gap` por candidato e totalizar `pncp_gap_leads` no relatório da fila.
- [x] Testes aprovados no workflow `Test auction adapters` execução **41712403785**.
- [ ] Validar a API PNCP e novos candidatos em coleta completa (arquivo `app/pncp-candidates.json` ainda não publicado).
- [ ] Validar diagnóstico DOM VIP na coleta completa (arquivo `app/vip-dom-diagnostics.json` ainda não publicado).
- [ ] Confirmar diretamente os editais PNCP de UFs ausentes antes de promover qualquer evento ao feed.

## Recuperação de fontes — 03/11/2026

- [x] Localizar a página de leilão **003/2026 da Prefeitura de Aracaju** no próprio leiloeiro RJ Leilões, ID 4845. Data 12/11/2026, início 09h30, com veículos entre os 22 lotes. Substituir o anúncio municipal que retornava evidências ausentes por URL individual da plataforma.
- [x] Substituir a página de Curitiba bloqueada (HTTP 403) pelo **catálogo oficial da Secretaria Municipal de Defesa Social e Trânsito**, com identificação específica do edital 17/2026.
- [x] Cadastrar editais adicionais de Curitiba: **16/2026 — sucatas inservíveis (11/11 às 9h)** e **18/2026 — veículos e sucatas (25/11 às 9h)**.
- [x] Evitar inferir número de veículos a partir do número total de lotes; `vehicle_count=null` para fontes sem contagem comprovada.
- [x] Adicionar testes offline de evidência por edital, horário confirmado de Aracaju e prevenção de confusão entre cidades. Workflow **41712930282 aprovado**.
- [ ] Verificar recuperação destas fontes em coleta real; não adicionar os três eventos ao total confirmado antes do relatório.
- [ ] Validar API PNCP em rede e confirmar candidatos reais com documentação original; `app/pncp-candidates.json` ainda não existe na última consulta.

## Última coleta confirmada — 03/11/2026, 17h07 BRT

- Workflow `Collect verified auctions` executado com sucesso, inclusive testes, browser e publicação.
- **39 leilões únicos, 91 registros, 18 UFs**, de acordo com o relatório da coleta (redução temporária em relação aos 41 anteriores).
- **Copart:** 10 eventos, todos com URL individual de venda oficial; exemplos em Goiânia mostram duas vendas distintas no mesmo pátio e dia.
- **VIP:** 15 eventos, 67 registros multiestaduais, **0 links individuais**. Log: `VIP DOM: 0 candidate card(s)`; fallback da agenda manteve a coleta.
- Freitas: 3 eventos. Fila RSS: 113 pistas, sem publicação automática.
- Fontes oficiais: 13/20 validadas; 7 falhas (Curitiba 403, duas PRF-SP timeout, PRF-ES 429, Aracaju sem evidências, Pedranópolis 403, Superbid 403).
- `direct_event_links=10`, `calendar_links=67`, `curated_source_links=14` no relatório.
- **Após essa coleta:** busca de cartões VIP ampliada a folhas com data ou rótulo em elementos separados; diagnóstico de estrutura DOM `app/vip-dom-diagnostics.json` quando nenhum cartão for localizado; HTTP 429 passa a aguardar próxima coleta sem nova tentativa via navegador. Alterações aguardam execução.

## Atualização de triagem — 03/11/2026

- Última coleta completa ainda: **39 eventos únicos em 18 UFs**; o novo arquivo `app/vip-dom-diagnostics.json` ainda não foi produzido em coleta real.
- O pipeline de descoberta passa a despriorizar notícias de leilões já encerrados quando o título identifica data passada, como o caso “próximo dia 28” publicado em outubro.
- Datas extraídas de manchetes são **somente pistas de revisão** (`date_hint_status=headline_only_unverified`), nunca publicadas diretamente no feed.
- Testes Python da nova triagem concluíram com sucesso no GitHub Actions: execução `41711104446`.

## Próximas entregas

1. Validar `app/pncp-candidates.json` na próxima coleta e selecionar editais de veículos de municípios ainda não cobertos para confirmação independente.
2. Validar o novo detector de cartões VIP e seu diagnóstico DOM; se zero cartões, usar evidências para adaptar o coletor, sem inventar links.
3. Medir a proporção de links diretos Copart/VIP e manter links de calendário somente onde a URL individual não for observável.
4. Encontrar fontes alternativas públicas para Aracaju, Curitiba, Pedranópolis e Superbid; não contornar HTTP 403.
5. Converter notícias de órgãos oficiais em eventos somente após confirmar **data futura, estado, organizador e documento original**.
6. Auditar a qualidade das UFs associadas aos eventos multiestaduais da VIP.

**Atualização:** parser VIP isolado por cartão publicado em 03/11/2026, ainda sem nova coleta. A página da agenda apresentou redirecionamento em loop na inspeção externa, portanto a captura de URL individual não está confirmada.

**Novidade:** adaptador de descoberta da API PNCP oficial publicado em 03/11/2026; testes aprovados, coleta de rede ainda não validada. `app/pncp-candidates.json` será gerado na próxima execução e jamais será misturado automaticamente ao feed verificado.

**Regra:** a execução ser bem-sucedida não equivale a cobertura nacional completa.


## Incidente do workflow — 03/11/2026

- [x] Diagnosticar execução #16: 27 testes Python aprovados, 2 testes de cartões VIP falharam; a coleta nem foi iniciada.
- [x] Corrigir fixtures com novas linhas reais nos testes VIP (`test_vip_card_uses_single_official_detail_link`, `test_vip_ambiguous_link_stays_calendar`).
- [x] Confirmar workflow `Test auction adapters` após correção: execução 41709418273 **sucesso**.
- [x] Confirmar execução de `Collect verified auctions` em 03/11/2026 às 17h07 BRT — sucesso; 39 eventos únicos, 18 UFs.
- [x] Diferenciar a execução que falhou das coletas bem-sucedidas posteriores.

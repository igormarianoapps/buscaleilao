# BuscaLeilão — checklist do projeto

Atualizado em 03/11/2026. **Implementado** significa código publicado no GitHub; execução e cobertura reais dependem do próximo relatório.

## Marco do MVP — critérios de lançamento

**Produto:** agenda nacional de **eventos de leilão de veículos**, não catálogo de lotes. Público consegue filtrar por UF e data e consultar a fonte. O produto não promete listar todos os leilões do Brasil.

**Estado em 03/11/2026:** pré-MVP funcional. Coleta completa #41715100215 aprovada às 17h43 BRT: **48 eventos únicos, 111 registros, 19 UFs, 19/22 fontes curadas verificadas**, Copart 12, VIP 16, Freitas 3, Curitiba 3. PNCP descobriu 25 candidatos ainda não publicados. **P0.1 concluído; P0.2 em 1/3.**

### P0 — Bloqueadores para lançamento público

- [x] **P0.1 — Uma execução ponta a ponta** do workflow atual deve passar por testes, Copart, VIP/Freitas, PNCP, fila de revisão e publicação. Conferir todos os arquivos produzidos e logs, especialmente `app/pncp-candidates.json` e `app/vip-dom-diagnostics.json` (quando houver fallback).
- [ ] **P0.2 — Estabilidade:** observar 3 coletas completas consecutivas com sucesso do workflow e feed atualizado dentro de 24h; a falha de uma fonte não pode bloquear o feed. Registrar taxa de fontes recuperadas e motivos de falha.
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
- [ ] **P0.2:** 1/3 coletas completas consecutivas bem-sucedidas; faltam duas execuções posteriores com sucesso e feed atualizado em até 24h.
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

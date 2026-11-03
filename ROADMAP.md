# BuscaLeilão — checklist do projeto

Atualizado em 03/11/2026. **Implementado** significa código publicado no GitHub; execução e cobertura reais dependem do próximo relatório.

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
- [ ] Encontrar fonte de Curitiba acessível ao coletor (HTTP 403 na última tentativa)

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

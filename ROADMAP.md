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
- [ ] Confirmar URLs e IDs individuais da VIP após coleta real; manter link de calendário como fallback
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
- [ ] Criar adaptadores próprios para outros leiloeiros com calendário público verificável
- [ ] Automatizar conversão de notícias em candidaturas com data, UF, documento e URL original validados
- [x] Incluir relatório de UFs sem eventos e percentual de presença, sem confundir isso com cobertura de mercado
- [ ] Medir cobertura de leiloeiros/prefeituras por UF; não confundir presença em UF com cobertura completa
- [ ] Encontrar fonte de Curitiba acessível ao coletor (HTTP 403 na última tentativa)

## Última coleta confirmada — 03/11/2026, 16h40 BRT

- **41 leilões únicos**, 92 registros estaduais, 19 UFs com pelo menos um evento (70,4% de presença geográfica, não cobertura total).
- Coleta privada: VIP 15, Copart 9, Freitas 3. Órgãos públicos: 14.
- **16 de 20** anúncios curados aprovados; falhas independentes em Curitiba (403), Aracaju (evidências ausentes), Pedranópolis (403), Superbid (403).
- DETRAN-BA, DETRAN-GO e Serranópolis do Iguaçu entraram no feed.
- Fila de pesquisa: 80 notícias; nenhuma publicada sem validação.
- `app/source-health.json` foi criado e permite diagnosticar erros por fonte.
- Código de deduplicação por URL individual atualizado **após** esta coleta; ainda não validado em nova execução.

## Próximas entregas

1. Executar coleta completa para medir quantos links específicos Copart foram identificados e se dois leilões do mesmo pátio/dia deixaram de ser agrupados.
2. Verificar diagnósticos de cartões VIP na execução automática: número de cartões reconhecidos, registros validados e URLs específicas; se não houver URL individual, manter a agenda.
3. Encontrar fontes alternativas públicas para Aracaju, Curitiba, Pedranópolis e Superbid; não contornar HTTP 403.
4. Converter notícias de órgãos oficiais em eventos somente após confirmar **data futura, estado, organizador e documento original**.
5. Auditar a qualidade das UFs associadas aos eventos multiestaduais da VIP.

**Atualização:** parser VIP isolado por cartão publicado em 03/11/2026, ainda sem nova coleta. A página da agenda apresentou redirecionamento em loop na inspeção externa, portanto a captura de URL individual não está confirmada.

**Regra:** a execução ser bem-sucedida não equivale a cobertura nacional completa.


## Incidente do workflow — 03/11/2026

- [x] Diagnosticar execução #16: 27 testes Python aprovados, 2 testes de cartões VIP falharam; a coleta nem foi iniciada.
- [x] Corrigir fixtures com novas linhas reais nos testes VIP (`test_vip_card_uses_single_official_detail_link`, `test_vip_ambiguous_link_stays_calendar`).
- [ ] Confirmar resultado do workflow `Test auction adapters` disparado pelo commit corretivo e da próxima coleta.
- [ ] Não interpretar o relatório anterior (41 eventos/19 UFs) como resultado desta execução falha.

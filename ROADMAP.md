# BuscaLeilão — checklist do projeto

Atualizado em 03/11/2026. **Implementado** significa código publicado no GitHub; execução e cobertura reais dependem do próximo relatório.

## Fase 1 — Motor de coleta e qualidade

- [x] Coletores independentes: erro de uma fonte não interrompe a verificação das outras
- [x] Verificação paralela limitada para anúncios oficiais
- [x] Uma consulta HTTP por URL: páginas compartilhadas são reaproveitadas
- [x] Fallback Chromium para erro de rede ou texto dinâmico, sem desativar HTTPS nem insistir em HTTP 403/401
- [x] Histórico de saúde por fonte: último sucesso, erro e falhas consecutivas em `app/source-health.json`
- [x] Não publicar anúncio sem as evidências configuradas; não manter como confirmado um evento indisponível
- [x] Testes unitários de isolamento, cache de páginas, erro 403, fallback e cancelamento
- [x] Executar testes Python no workflow de coleta **antes** de atualizar o feed
- [x] Deduplicação de registros multiestaduais somente com mesmo `event_id`
- [ ] Validar arquitetura nova e coletor Freitas em execução completa do GitHub Actions
- [ ] Links individuais estáveis e IDs originais da Copart e VIP
- [ ] Detectar adiamentos e cancelamentos com o edital original
- [ ] Quantidades de veículos apenas quando comprovadas pela fonte

## Fase 2 — Cobertura nacional

- [x] Coleta pública inicial de Copart e VIP
- [x] Fontes oficiais curadas: prefeituras, PRF e Detrans (lista em `app/sources.json`)
- [x] Acrescentar leilões de pequenos municípios: Serranópolis do Iguaçu/PR e Pedranópolis/SP (novos, aguardando execução)
- [x] Descoberta RSS direcionada para UFs em rodízio até percorrer os 27 entes federativos
- [x] Fila de triagem recente em `app/review-queue.json`, sem publicação automática de notícias
- [ ] Extrair identificadores e URLs específicos da Copart/VIP
- [x] Implementar um adaptador independente de calendário da Freitas Leiloeiro, validando data/UF na página individual; aguarda execução real
- [x] Adicionar páginas oficiais específicas da Freitas (dois eventos) e Superbid (um evento), sujeitas à verificação do coletor
- [ ] Criar adaptadores próprios para outros leiloeiros com calendário público verificável
- [ ] Automatizar conversão de notícias em candidaturas com data, UF, documento e URL original validados
- [x] Incluir relatório de UFs sem eventos e percentual de presença, sem confundir isso com cobertura de mercado
- [ ] Medir cobertura de leiloeiros/prefeituras por UF; não confundir presença em UF com cobertura completa
- [ ] Encontrar fonte de Curitiba acessível ao coletor (HTTP 403 na última tentativa)

## Marco de validação

**Última coleta confirmada, antes desta entrega:** 03/11/2026 às 15h14 BRT — 30 eventos únicos, 18 UFs, 52 notícias na fila de revisão. O feed muda a cada execução e datas passadas saem naturalmente.

**Próxima verificação conjunta:** a ação `Collect verified auctions` executará testes e produzirá feed, relatório e `source-health.json`. Conferir também links específicos de Freitas/Superbid, resultados do novo coletor Freitas, Serranópolis do Iguaçu e Pedranópolis, estabilidade das outras fontes e ausência de publicações sem evidência. Não depende de execução manual após cada commit.

## Definição de MVP

Busca por UF e data; eventos distintos e verificáveis; origem oficial acessível; atualização automática duas vezes ao dia; diagnósticos de falha por fonte; cobertura nacional medida, sem prometer 100% dos leilões.

# BuscaLeilão — checklist de execução

Atualizado: 03/11/2026. Status abaixo indica código publicado, **não** validação do deploy em produção.

## Fase 1 — Qualidade dos dados

- [x] Impedir agrupamento por simples coincidência de categoria, data e horário; somente eventos com `event_id` explícito podem ser agrupados.
- [x] Compartilhar o mesmo `event_id` entre estados de um registro VIP identificado no mesmo bloco público.
- [x] Não transformar quantidades de lotes em quantidades de veículos.
- [x] Relatório de quantidade de eventos únicos, organizadores e UFs com resultados.
- [ ] Obter URL individual estável de **cada** evento da VIP e Copart.
- [ ] Separar corretamente múltiplos leilões semelhantes com dados idênticos e revisar captura de UFs.
- [ ] Extrair contagem de veículos apenas de campos comprovados.
- [ ] Identificar e acompanhar cancelamentos, alterações de datas e lotes.
- [x] Testar a extração anterior no GitHub Actions: 24 eventos únicos, 17 UFs (relatório 02/11/2026).
- [x] Validar no GitHub Actions a nova rotina de recuperação por Chromium (03/11/2026): Lorena recuperada; Curitiba continua com timeout.
- [ ] Corrigir timeout persistente de Curitiba sem desativar TLS.

## Fase 2 — Cobertura nacional

- [x] Ampliar consultas RSS para leiloeiros, órgãos federais, municípios e regiões fora dos quatro estados iniciais.
- [x] Adicionar Curitiba SMDT 17/2026 (PR) como fonte oficial monitorada.
- [x] Adicionar sessões PRF-SP 03/11 e 04/11/2026 como fontes monitoradas.
- [x] Ordenar possíveis fontes oficiais para análise, sem publicar candidatos automaticamente.
- [x] Adicionar fontes oficiais DETRAN-BA (25/11) e PRF-ES (04/11): ambas verificadas na coleta de 03/11.
- [x] Tentar recuperação de falhas temporárias/SSL via navegador sem desativar validação de certificados.
- [ ] Converter candidatos RSS em eventos a partir de edital/data/UF verificados em escala.
- [ ] Adicionar conectores confiáveis de outros grandes leiloeiros e órgãos públicos.
- [ ] Expandir para municípios menores e monitorar cobertura das 27 UFs.
- [ ] Medir percentual de fontes acompanhadas; não prometer 100% de cobertura.

## Próxima entrega

1. Coleta de 03/11 validada: 27 eventos únicos, 58 registros estaduais, 18 UFs; **testes em workflow separado ainda não confirmados**.
2. Resolver Curitiba (timeout até com Chromium). Lorena, BA e ES já estão confirmados no feed.
3. Investigar links individuais/identificadores de Copart e VIP antes de expandir extração automática de novos leiloeiros.

Critério de conclusão: leilões exibidos correspondem a eventos reais, sem atribuição indevida a uma UF, e apontam para a fonte específica sempre que ela estiver disponível.

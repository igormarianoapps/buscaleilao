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
- [x] Encontrar página oficial alternativa para Curitiba (Guia Municipal, edital 17/2026); cadastrada, pendente de execução da coleta.
- [x] Verificar tentativa de recuperação de Curitiba: fonte alternativa respondeu HTTP 403; evento segue fora da agenda.
- [ ] Encontrar fonte pública acessível para Curitiba sem contornar controles de acesso.

## Fase 2 — Cobertura nacional

- [x] Ampliar consultas RSS para leiloeiros, órgãos federais, municípios e regiões fora dos quatro estados iniciais.
- [x] Adicionar Curitiba SMDT 17/2026 (PR) como fonte oficial monitorada.
- [x] Adicionar sessões PRF-SP 03/11 e 04/11/2026 como fontes monitoradas.
- [x] Ordenar possíveis fontes oficiais para análise, sem publicar candidatos automaticamente.
- [x] Adicionar fontes oficiais DETRAN-BA (25/11) e PRF-ES (04/11): ambas verificadas na coleta de 03/11.
- [x] Tentar recuperação de falhas temporárias/SSL via navegador sem desativar validação de certificados.
- [x] Melhorar triagem de RSS: excluir notícias com mais de 120 dias e priorizar somente domínios públicos reais.
- [x] Cadastrar e confirmar no coletor o edital de Campina Grande/PB e três sessões da Semob/Cuiabá-MT (03/11/2026).
- [ ] Converter candidatos RSS em eventos a partir de edital/data/UF verificados em escala.
- [ ] Adicionar conectores confiáveis de outros grandes leiloeiros e órgãos públicos.
- [ ] Expandir para municípios menores e monitorar cobertura das 27 UFs.
- [ ] Medir percentual de fontes acompanhadas; não prometer 100% de cobertura.

## Última execução verificada — 03/11/2026, 15h08 BRT

- 62 registros estaduais; **31 eventos únicos**, distribuídos por 18 UFs.
- Campina Grande/PB e três sessões de Cuiabá/MT validadas.
- 125 notícias candidatas (sem publicação automática); 0 erros RSS.
- Curitiba: HTTP 403 também com navegador; não publicada.
- Copart e VIP acessíveis.

## Próxima entrega

1. Localizar fonte alternativa de Curitiba **acessível publicamente**, sem desativar verificação TLS nem contornar o HTTP 403.
2. Triar as 125 pistas, priorizando órgãos oficiais e leilões futuros.
3. Obter links específicos e identificadores individuais de cada leilão nas grandes plataformas.

Critério de conclusão: apenas eventos cuja data/UF e fonte estejam verificadas entram na agenda.

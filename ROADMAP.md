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
- [ ] Encontrar fonte pública acessível para Curitiba sem contornar controles de acesso. Edital 17/2026 confirmado na página municipal, porém o coletor recebe HTTP 403.

## Fase 2 — Cobertura nacional

- [x] Ampliar consultas RSS para leiloeiros, órgãos federais, municípios e regiões fora dos quatro estados iniciais.
- [x] Adicionar Curitiba SMDT 17/2026 (PR) como fonte oficial monitorada.
- [x] Adicionar sessões PRF-SP 03/11 e 04/11/2026 como fontes monitoradas.
- [x] Ordenar possíveis fontes oficiais para análise, sem publicar candidatos automaticamente.
- [x] Adicionar fontes oficiais DETRAN-BA (25/11) e PRF-ES (04/11): ambas verificadas na coleta de 03/11.
- [x] Tentar recuperação de falhas temporárias/SSL via navegador sem desativar validação de certificados.
- [x] Melhorar triagem de RSS: excluir notícias com mais de 120 dias e priorizar somente domínios públicos reais.
- [x] Cadastrar e confirmar no coletor o edital de Campina Grande/PB e três sessões da Semob/Cuiabá-MT (03/11/2026).
- [x] Criar fila de revisão `app/review-queue.json`, priorizando notícias recentes e fontes governamentais, sem publicá-las como eventos.
- [x] Cadastrar o leilão municipal de Aracaju/SE (12/11).
- [x] Adicionar segunda verificação com navegador para páginas oficiais que não mostram a evidência esperada no HTML estático (Aracaju); **pendente de validar na próxima coleta**.
- [ ] Confirmar Aracaju em execução real, sem dispensar nenhuma evidência.
- [x] Revisar candidatos: notícias do Detran-PR (28/10) e Detran-RS (21/10) já estavam vencidas em 03/11 e foram descartadas.
- [x] Cadastrar DETRAN-GO nº 03/2026, 09/11 às 9h, com 2.189 veículos documentados em fonte oficial (aguardando coleta).
- [ ] Converter candidatos RSS em eventos a partir de edital/data/UF verificados em escala.
- [ ] Adicionar conectores confiáveis de outros grandes leiloeiros e órgãos públicos.
- [ ] Expandir para municípios menores e monitorar cobertura das 27 UFs.
- [ ] Medir percentual de fontes acompanhadas; não prometer 100% de cobertura.

## Última execução verificada — 03/11/2026, 15h14 BRT

- **30 eventos únicos**, 61 registros, 18 UFs.
- 92 descobertas RSS; 52 pistas priorizadas para revisão; nenhuma publicada automaticamente.
- Falhas: Curitiba (HTTP 403), DETRAN-BA (timeout), Aracaju (evidências ausentes).
- Copart e VIP mantiveram coleta de eventos.

## Próxima entrega

1. **Rodar testes e coleta** para validar o novo DETRAN-GO, segunda tentativa de leitura do DETRAN-BA e fallback seguro de Aracaju.
2. Conferir `app/collection-report.json`; nenhum evento deve entrar sem as evidências cadastradas.
3. Continuar revisão das notícias futuras da fila, evitando leilões já encerrados; localizar URLs individuais nas plataformas.
4. Curitiba permanece bloqueada por HTTP 403 e depende de fonte oficialmente acessível.

**Última execução confirmada (anterior a estes commits):** 30 eventos únicos, 18 UFs, 52 notícias priorizadas. Novas alterações ainda não validadas pelo workflow.

Critério: eventos com data, estado e fonte verificados; não extrapolar número de lotes para número de veículos.

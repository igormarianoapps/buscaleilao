# BuscaLeilão

**Agenda brasileira de leilões de veículos**, não um catálogo de veículos ou lotes. Busca por UF e data, com acesso à fonte responsável pelo anúncio.

Site: https://buscaleilao-nine.vercel.app/

## Catálogo de plataformas (branch develop, novembro/2026)

O registro `app/auction-platforms.json` acompanha os **16 sites indicados pelo usuário**, distribuídos entre Centro-Oeste, São Paulo, Sul/Sudeste e integrações já existentes. O monitor `scripts/auction_platform_watch.py` registra disponibilidade e **candidatos não verificados** em `app/auction-platform-diagnostics.json` — esses candidatos **não entram em `events.json`**.

- **Integrações já existentes:** Copart, Freitas e VIP, sujeitas à validação de URL individual em cada coleta.
- **Novos coletores com publicação restrita a eventos confirmados:** Vardana (`scripts/regional_collect.py`) e Bolsa de Leilões (`scripts/bolsa_collect.py`). A Claudio Kuss é verificada pelo mesmo coletor regional, mas eventos sem lotes publicados não são anunciados.
- **Outras plataformas:** Leilo, MC Leilão, Flex, Parque dos Leilões, Sodré Santoro, Loop Brasil, Milan, Hisa, Palácio dos Leilões e Rogério Menezes. Cada uma tem domínio monitorado, mas ainda necessita de extrator por evento com evidência de data e lotes para publicação automática. Algumas restringem acesso de robôs; esse bloqueio é respeitado.
- **Diretório público `/fontes`:** lista os 16 sites e explica as diferenças entre fonte monitorada e leilão verificado.

**Importante:** um domínio na lista não comprova que o leiloeiro esteja habilitado. Os eventos podem ocorrer em outras UFs; nunca classificar pelo estado da sede do site. A aprovação é feita por **evento e link**, não apenas por domínio. O monitoramento não deve ser confundido com cobertura integral da agenda.

## Arquitetura atual

- `app/index.template.html` + `app/agenda.mjs`: frontend fonte, filtros por UF e intervalo de datas, e agrupamento por evento explícito.
- `scripts/build_static_page.py`: gera `app/index.html` autossuficiente com o feed verificado e filtros embutidos; evita falhas de caminhos de assets da hospedagem estática. **Editar o template, não apenas o HTML gerado.**
- `app/events.json`: feed **somente com eventos validados** na última coleta.
- `app/sources.json`: anúncios oficiais curados com evidências específicas de cada evento.
- `scripts/source_collector.py`: verifica várias fontes com paralelismo limitado, reutiliza URLs repetidas, e isola erros. Para páginas dinâmicas, usa Chromium **sem contornar restrições de acesso**.
- `scripts/browser_collect.py`: adaptadores experimentais dos calendários públicos Copart e VIP, com coletor independente da Freitas.
- `scripts/freitas_collect.py`: encontra páginas de leilões da Freitas no calendário público e só aceita eventos de veículos com data de encerramento, horário e UF extraídos da página específica.
- `app/sources.json` também inclui eventos específicos de Freitas e Superbid, verificados a cada execução.
- `scripts/collect.py`: coordena ambos os coletores e publica feed, `app/collection-report.json` e `app/source-health.json`.
- `scripts/discover.py`: descobre notícias de leilões, incluindo rodízio regional das 27 UFs.
- `scripts/prioritize_leads.py`: cria `app/review-queue.json` com notícias recentes para verificação. **Nunca publica notícias como leilões.**
- `.github/workflows/collect.yml`: roda testes Python, atualiza fontes, gera HTML autossuficiente, diagnósticos, descobertas e feed em um único workflow; agenda diária duas vezes.
- `.github/workflows/smoke-public.yml`: testa manualmente a página **publicada** em Chromium, incluindo lista inicial, estados, filtros por período e botão de limpar.
- `.github/workflows/test.yml`: testes Python e Node nas alterações de código.

## Regra de confiança

Um evento só entra na agenda se as evidências da fonte corresponderem. Uma fonte que falhar não interrompe as demais, mas o evento que ela não conseguiu confirmar **não permanece como verificado** só porque esteve no feed anterior. Erros HTTP 401/403, bloqueios e problemas HTTPS não são contornados. Horário e quantidade de veículos ficam vazios quando indisponíveis; número de lotes não é automaticamente número de veículos.

A presença de eventos em uma UF não significa que todos os leilões daquele estado foram encontrados. Identificadores/links individuais de Copart e VIP ainda requerem melhorias. Eventos de Freitas/Superbid já cadastrados usam URLs individuais, mas a extração automática da Freitas ainda precisa ser validada em produção.

## Operação

Abra [Collect verified auctions](https://github.com/igormarianoapps/buscaleilao/actions/workflows/collect.yml) e execute o workflow quando necessário. Os seguintes arquivos permitem auditar o resultado:

- `app/collection-report.json`: quantidade total, eventos únicos, UFs com/sem eventos, percentual de presença por UF e falhas. Presença por UF não significa cobertura total de leilões.
- `app/source-health.json`: histórico de verificação por fonte, último sucesso e erros consecutivos.
- `app/browser-diagnostics.json`: acessibilidade e datas visualizadas nos sites de plataforma.
- `app/review-queue.json`: fila de pesquisa, **não** eventos confirmados.

Os testes automatizados precisam ser aprovados antes da publicação do feed na rotina de coleta.

## Próximas metas

Consultar o [ROADMAP.md](ROADMAP.md) atualizado: melhorar links e identidade dos eventos, converter mais anúncios em eventos confirmados, adicionar coletores independentes de outros leiloeiros e medir cobertura nacional.

A aplicação FastAPI/SQLite em `app/main.py` é um protótipo separado: o frontend publicado utiliza o feed estático, não a base SQLite.

## Links de leilões (novembro de 2026)

A Copart agora tem extração de URL específica da venda quando a tabela pública disponibiliza o link; caso contrário, permanece o calendário. Eventos distintos do mesmo pátio e dia são separados pelo identificador da venda. A VIP permanece com link da agenda até termos URL específica comprovada. Essas alterações dependem de execução do workflow para validação final.

## Descoberta nacional por editais do PNCP (experimental)

O pipeline inclui `scripts/discover_pncp.py`, que consulta a API pública oficial do Portal Nacional de Contratações Públicas para leilões eletrônicos (modalidade 1) e presenciais (13). O script pesquisa publicações recentes e seleciona apenas objetos com indício explícito de veículo, situação não cancelada, UF definida e data futura de encerramento de propostas. Os resultados são gravados em `app/pncp-candidates.json`, com identificador de controle PNCP e URL do edital para revisão. **Nenhum candidato é publicado automaticamente em `app/events.json`**: o encerramento das propostas pode não ser a data exata do leilão, e o edital deve ser revisado antes da publicação. A primeira execução em rede ainda não foi confirmada.

A fila RSS também ignora manchetes com data de leilão claramente passada e dá prioridade a datas futuras explícitas, sem tratá-las como confirmação.

## Integração dos 16 sites — controles de qualidade

- `scripts/leilo_collect.py`: agrega lotes da edição atual de leilões de veículos, utiliza a UF de cada lote e revalida data e hora; URLs de lotes isolados não são eventos.
- `scripts/secondary_collect.py`: adapta Parque dos Leilões, Flex e Hisa. Publica apenas se confirmar data, endereço ou localização do evento e lotes veiculares na página individual.
- `scripts/platform_triage.py` e `scripts/platform_review.py`: classificam notícias, categorias, lotes isolados e candidatos sem promoção automática para a agenda.
- `scripts/platform_quality.py`: registra por site disponibilidade, eventos distintos confirmados, candidatos, rejeições e limitações; os dados ficam em `app/platform-quality.json`.
- **Regra de segurança:** coletor e rota oficial específica precisam concordar; lista de domínios não certifica o leiloeiro. Consulte registros oficiais antes de participar.
- As fontes que não liberam dados verificáveis permanecem monitoradas, mas não são declaradas como integrações completas.

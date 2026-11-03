# BuscaLeilão

**Agenda brasileira de leilões de veículos**, não um catálogo de veículos ou lotes. Busca por UF e data, com acesso à fonte responsável pelo anúncio.

Site: https://buscaleilao-nine.vercel.app/

## Arquitetura atual

- `app/index.html` + `app/agenda.mjs`: frontend estático, filtro de UF/data e agrupamento por evento explícito.
- `app/events.json`: feed **somente com eventos validados** na última coleta.
- `app/sources.json`: anúncios oficiais curados com evidências específicas de cada evento.
- `scripts/source_collector.py`: verifica várias fontes com paralelismo limitado, reutiliza URLs repetidas, e isola erros. Para páginas dinâmicas, usa Chromium **sem contornar restrições de acesso**.
- `scripts/browser_collect.py`: adaptadores experimentais dos calendários públicos Copart e VIP, com coletor independente da Freitas.
- `scripts/freitas_collect.py`: encontra páginas de leilões da Freitas no calendário público e só aceita eventos de veículos com data de encerramento, horário e UF extraídos da página específica.
- `app/sources.json` também inclui eventos específicos de Freitas e Superbid, verificados a cada execução.
- `scripts/collect.py`: coordena ambos os coletores e publica feed, `app/collection-report.json` e `app/source-health.json`.
- `scripts/discover.py`: descobre notícias de leilões, incluindo rodízio regional das 27 UFs.
- `scripts/prioritize_leads.py`: cria `app/review-queue.json` com notícias recentes para verificação. **Nunca publica notícias como leilões.**
- `.github/workflows/collect.yml`: roda testes Python, atualiza fontes, diagnósticos, descobertas e feed em um único workflow; agenda diária duas vezes.
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

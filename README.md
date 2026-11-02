# BuscaLeilão — MVP inicial

Agenda nacional de eventos de leilão de veículos (não é catálogo de lotes).

## O que já funciona
- Interface responsiva de busca por UF e data.
- API FastAPI com endpoint `/api/auctions` e `/api/health`.
- Persistência local em SQLite para armazenar leilões.
- Nenhum evento inventado: a base começa vazia.

## Rodar localmente
Requer Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Acesse http://localhost:8000 e a documentação em http://localhost:8000/docs.

## Próximo passo — prioridade alta
Criar um pipeline de descoberta e coleta que:
1. Registre fontes (sites oficiais de prefeituras, DETRANs, diários oficiais e leiloeiros).
2. Use APIs e HTML quando possível, PDFs com texto extraível quando necessário e browser automatizado apenas para páginas dinâmicas.
3. Extraia **eventos** e respectivos dados (UF, data, hora, quantidade de veículos se disponível, organizador e link).
4. Valide contra a fonte original, registre última verificação, deduplique e atualize cancelamentos.
5. Faça descobertas recorrentes de novas fontes com monitoramento de falhas, respeitando limites e condições de acesso.

**Observação:** este scaffold ainda não realiza coleta na internet. Não afirmar cobertura nacional antes de medir fontes e eventos coletados.

## Coleta automática (primeira iteração)
- Fontes municipais documentadas em `app/sources.json`, com evidências exigidas por fonte.
- `scripts/collect.py` visita páginas HTML públicas, confere as evidências e publica `app/events.json`.
- GitHub Actions: `.github/workflows/collect.yml`, duas vezes ao dia ou execução manual em **Actions → Collect verified auctions → Run workflow**.
- `app/collection-report.json` registra erros e bloqueios. Sites bloqueados não são contornados e eventos sem evidência são ignorados.
- O frontend consulta `/app/events.json` diretamente; verifique se essa rota é publicada na Vercel.
- O script ainda **não descobre automaticamente novas fontes**, nem interpreta cancelamentos com precisão; a confirmação de status requer inspeção do edital.
- O feed começa vazio e só é preenchido após uma execução bem-sucedida do workflow.

## Descoberta automática (experimental)
`scripts/discover.py` pesquisa RSS público por leilões de veículos. Os links vão para `app/discovery-candidates.json` como **candidatos não verificados** e não aparecem na agenda. Ainda é necessário validar manualmente links, data, quantidade e existência do evento, além de cadastrar coletores por fonte.

Não desativar a verificação de SSL para contornar erros de certificado. O site de Lorena permanece como falha reportada até ter uma fonte acessível e confiável.

## Cobertura de leiloeiros privados
`scripts/platforms.py` inclui adaptadores iniciais para calendários públicos de **Copart** e **VIP Leilões**. Eles extraem eventos, datas e estados, sem consultar lotes individuais. Quantidades de veículos permanecem não informadas quando a fonte divulga apenas lotes. Para leilões multiestaduais, um mesmo evento é indexado em cada UF mencionada. Falhas de acesso aparecem no relatório; não há garantia de cobertura integral ou validação em produção até a execução do workflow.

A meta é incluir **grandes e pequenos leiloeiros, instituições e órgãos públicos**. A cobertura nacional completa depende do cadastro contínuo de fontes e de validadores confiáveis.

## Diagnóstico de acesso com navegador
O workflow agora executa `scripts/browser_probe.py` usando Chromium/Playwright, guardando `app/browser-diagnostics.json` (URLs finais, códigos HTTP, quantidade de datas/tabelas e amostras públicas de texto). Esse relatório **não incorpora eventos automaticamente**: permite desenvolver adaptadores com base no HTML realmente renderizado e identificar bloqueios/loops sem contorná-los.

## Coletores Playwright (versão experimental)
O pipeline principal usa agora `scripts/browser_collect.py` para extrair calendários públicos da Copart e VIP em Chromium. Eventos são filtrados por data futura e UF identificada; quantidades de lotes não são tratadas como quantidades de veículos. O workflow precisa concluir para validar quantos eventos foram coletados. Não há garantia de cobertura total: datas/estados ou identificadores ausentes fazem o evento ser descartado.

## Agenda de eventos únicos
O frontend agrupa registros da VIP que compartilham dia, horário e categoria, mas são indexados por várias UFs; permite filtrar por qualquer UF incluída. O filtro de organizadores separa Copart, VIP e fontes municipais. O arquivo bruto `app/events.json` pode ter mais linhas que o número mostrado no app porque inclui indexação por UF. **Limitação:** se dois eventos distintos tiverem a mesma categoria, data e horário na VIP, o agrupamento pode uni-los; a correção definitiva depende da captura do identificador único/link específico de cada evento.

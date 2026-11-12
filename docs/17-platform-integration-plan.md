# Plano de integração — 17 sites do BuscaLeilão

Objetivo: publicar eventos veiculares realmente ativos, com edição, data, horário, local e link individual confirmado. Não confundir monitoramento com extração funcional. Trabalhar somente na develop; publicar na main após aprovação.

## 1. Integrações individuais pendentes

| Site | Trabalho técnico |
|---|---|
| Leilo | Revalidar cada edição recorrente, estados por lote e deduplicação com PMKLog |
| MC Leilão | Investigar SPA e obter calendário/IDs de evento em fonte pública |
| Flex | Extrair local verificável do evento e lotes, respeitando URL canônica |
| Parque dos Leilões | Conectar agenda, categoria e página individual com lotes |
| Sodré Santoro | Identificar eventos individuais nas páginas JS, descartar categorias |
| Copart | Revalidar IDs, lotes, datas de venda e URLs diretas |
| Loop Brasil | Inspecionar agenda pública e criar adaptador por evento |
| Freitas | Confirmar cobertura, edições, categorias e links diretos |
| Milan | Buscar feed/acesso público legítimo; pedir autorização/API se bloquear |
| VIP | Revalidar ID, data e endereço direto de cada edição |
| Hisa | Separar veículos de outras categorias e validar lotes e data |
| Bolsa | Ampliar eventos regionais e UFs reais dos veículos |
| Vardana | Conferir novas edições, lotes e expiração |
| Claudio Kuss | Aguardar lotes publicados e confirmar edição real |
| Palácio dos Leilões | Extrair data, categoria e lotes de páginas individuais já identificadas |
| Rogério Menezes | Detectar surgimento de eventos e novos links específicos |
| PMKLog | NOVO: mapear agenda pública, páginas /leilao/evento/ e IDs de edição, confirmar lotes, edital e excluir evento antigo de 09/11/2026 |

## 2. Padrão de dados e segurança

- Cada adaptador executa descoberta, busca do evento, validação de lotes e normalização.
- Salvar ID do evento, ID da edição, organizador, data, tipo de data, horário, cidade/UF dos lotes, contagem somente quando verificável, URL individual, status e última verificação.
- Nunca atribuir UF pela sede; nunca inferir data do ano corrente para edições antigas; distinguir abertura e encerramento.
- Ignorar notícias, home, agenda genérica, lotes soltos, cancelados, leilões anteriores e categorias não veiculares.
- Identificar duplicidade entre Leilo/PMKLog e anúncios oficiais do Detran-GO por edição, edital e identificação da venda.
- Não contornar login, CAPTCHA, proteção anti-bot ou bloqueios; documentar limitações e procurar canais de dados autorizados.

## 3. Operação contínua

- Executar coleta 2 vezes ao dia e checagem dos eventos ativos antes da sua realização.
- Emitir diagnóstico individual: disponível, sem leilões, bloqueado, parser mudou, dados insuficientes, publicado.
- Registrar sucessos, falhas, alertas por origem e manter a última agenda válida quando a nova coleta falhar.
- Deduplicar eventos e remover vencidos; impedir que uma falha de origem derrube todas as outras.
- Criar testes com fixtures por site: evento válido, expirado, sem lotes, edição recorrente, categoria errada e site bloqueado.

## 4. Homologação / conclusão

- Matriz com 17 fontes registradas, 17 resultados de diagnóstico e 17 cards em /fontes.
- Duas coletas consecutivas, testes Python e Node, validação de feed e smoke tests desktop/mobile.
- Meta: cada site possui coletor funcional ou limitação comprovada; só marcar 17 integrações operacionais com extração de dados legítima.
- Zero resultados é correto quando não existem eventos ativos. Não inventar eventos para cumprir meta.
- Nenhum merge na main antes de aprovação explícita.

## Nota específica da PMKLog

A PMKLog tem páginas de leilões recorrentes e lotes, mas a edição Detran-GO 09/11/2026 está concluída, sem próxima edição anunciada. Seu domínio já aparecia em regras legadas de links; o novo cadastro é monitoramento, não validação de coletor novo.

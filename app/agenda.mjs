/** Aggregate only records explicitly sharing the same event_id. Never guess identity. */
export function groupAuctions(items) {
  const grouped = new Map();
  for (const item of items || []) {
    if (!item || !item.id || !item.auction_date) continue;
    const key = item.event_id ? item.organizer + "|" + item.event_id : item.id;
    const states = (Array.isArray(item.states) ? item.states : [item.state]).filter(Boolean);
    if (!grouped.has(key)) {
      grouped.set(key, {...item, states: [...new Set(states)]});
    } else {
      const current = grouped.get(key);
      current.states = [...new Set([...current.states, ...states])];
    }
  }
  return [...grouped.values()].map(a=>({...a,states:a.states.sort()})).sort((a,b)=>
    a.auction_date.localeCompare(b.auction_date) ||
    (a.auction_time || '99:99').localeCompare(b.auction_time || '99:99') ||
    a.organizer.localeCompare(b.organizer));
}
export function normalizeSearch(value) {
  return String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim().replace(/\s+/g, ' ');
}
export function auctionDestination(a) {
  if (!a || a.link_verified !== true || a.destination_verified !== true) return null;
  const url = a.event_url || (a.source_link_type === 'event' || a.organizer === 'Freitas Leiloeiro' ? a.source_url : '');
  if (typeof url !== 'string' || !/^https:\/\/[^\s]+$/i.test(url)) return null;
  return url;
}
export function filterAuctions(items,{state='',start='',end='',day='',today='',keyword=''}={}) {
  const from=start || day || today;
  const to=end || day;
  if (from && to && from>to) return [];
  return groupAuctions(items).filter(a=>a.status==='scheduled' &&
    Boolean(auctionDestination(a)) &&
    (!today || a.auction_date>=today) &&
    (!state || a.states.includes(state)) &&
    (!from || a.auction_date>=from) &&
    (!to || a.auction_date<=to) &&
    (!keyword || normalizeSearch([a.title,a.city,a.organizer,a.id,a.event_id,a.auction_number,...a.states].join(' ')).includes(normalizeSearch(keyword))));
}

/** Freshness of the last successful collection, independent of event dates. */
export function feedFreshness(updatedAt, now = Date.now()) {
  const timestamp = Date.parse(updatedAt || '');
  if (!Number.isFinite(timestamp)) return {status:'unknown',ageHours:null};
  const ageHours = Math.max(0,(now-timestamp)/3600000);
  return {status:ageHours > 36 ? 'stale':'fresh',ageHours};
}

/** Use the source's actual provenance, never label all public sites as private. */
export function sourceLabel(type) {
  return ({
    municipal:'Prefeitura / órgão municipal',
    state:'Órgão estadual',
    federal:'Órgão federal',
    private:'Plataforma / leiloeiro privado',
  })[type] || 'Fonte pública';
}

/** Distinguish no upcoming auctions from a filtered-out result. */
export function emptyResultsMessage({state='',start='',end='',day='',keyword=''}={}) {
  if(keyword) return 'Nenhum leilão encontrado para esta palavra-chave e os filtros selecionados.';
  const hasDate=Boolean(start || end || day);
  if(state && hasDate) return 'Nenhum leilão encontrado para o estado e o período selecionados. Limpe os filtros para consultar outros eventos.';
  if(state) return 'Nenhum leilão encontrado para este estado. Limpe os filtros para consultar outros eventos.';
  if(hasDate) return 'Nenhum leilão encontrado para o período selecionado. Limpe os filtros para consultar outros eventos.';
  return 'Nenhum próximo leilão verificado na base atual. Consulte novamente após a próxima atualização.';
}

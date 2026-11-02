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
export function filterAuctions(items,{state='',day='',today=''}={}) {
  return groupAuctions(items).filter(a=>a.status==='scheduled' &&
    (!today || a.auction_date>=today) &&
    (!state || a.states.includes(state)) && (!day || a.auction_date===day));
}

/** Display one auction per event, even when VIP indexes it in several states. */
export function groupAuctions(items) {
  const grouped = new Map();
  for (const auction of items || []) {
    if (!auction || !auction.id || !auction.auction_date) continue;
    // VIP source IDs contain a state token before the final title slug.
    // Group only matching VIP records, never across organizers.
    const match = /^vip-(\d{4}-\d{2}-\d{2})-(\d{4})-([a-z]{2})-(.+)$/.exec(auction.id);
    const key = match
      ? ['vip', match[1], match[2], match[4], auction.source_url].join('|')
      : auction.id;
    if (!grouped.has(key)) {
      grouped.set(key, { ...auction, states: auction.states || [auction.state] });
    } else {
      const existing = grouped.get(key);
      if (!existing.states.includes(auction.state)) existing.states.push(auction.state);
    }
  }
  return [...grouped.values()].map(item => ({
    ...item, states: [...new Set(item.states)].sort()
  })).sort((a,b) =>
    a.auction_date.localeCompare(b.auction_date) ||
    (a.auction_time || '99:99').localeCompare(b.auction_time || '99:99') ||
    a.organizer.localeCompare(b.organizer));
}

export function filterAuctions(items, { state = '', day = '', today = '' } = {}) {
  return groupAuctions(items).filter(a =>
    a.status === 'scheduled' &&
    (!today || a.auction_date >= today) &&
    (!state || a.states.includes(state)) &&
    (!day || a.auction_date === day)
  );
}

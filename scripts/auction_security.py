"""Fail-closed auction destination policy. Review is per specific auction, not per domain alone."""
from urllib.parse import urlsplit, parse_qs
import re

# Curated organizers require both independently corroborated official notice
# and an individually approved event destination. No generic domain whitelist.
APPROVED_CURATED = {
    "cuiaba-semob-4-2026-11-11": (
        "www.cuiaba.mt.gov.br",
        "https://www.focoleiloes.com.br/leilao/497/lotes",
        "Prefeitura de Cuiabá — Semob",
        "2026-11-11",
    ),
    "detran-go-03-2026-11-09": (
        "goias.gov.br",
        "https://pmklog.com.br/leilao/evento/leilao-detran/?evento=fa724af3-d396-11f1-a2f8-02420a000014",
        "DETRAN Goiás",
        "2026-11-09",
    ),
}
def normalized_url(url):
    if not isinstance(url,str) or not url or any(c.isspace() for c in url):
        return None
    try:
        p=urlsplit(url)
        if (p.scheme!='https' or not p.hostname or p.username or p.password
                or p.port not in (None,443) or p.fragment or '\\' in url):
            return None
        if not re.fullmatch(r'[a-z0-9.-]+',p.hostname) or '..' in p.hostname:
            return None
        return p
    except ValueError:
        return None

def valid_destination(row):
    """Reject news, homepages, typosquatting, unreviewed sources and calendars."""
    original=normalized_url(row.get('source_url'))
    target=normalized_url(row.get('event_url') or row.get('source_url'))
    if not original or not target: return False
    org=row.get('organizer')
    if org=='Copart':
        from browser_collect import copart_detail_url
        return (not row.get('event_url') and row.get('source_link_type')=='event'
                and target.hostname in ('copart.com.br','www.copart.com.br')
                and copart_detail_url(row['source_url'],row.get('auction_date')) is not None)
    if org=='VIP Leilões':
        from browser_collect import vip_detail_url
        return (not row.get('event_url') and row.get('source_link_type')=='event'
                and target.hostname in ('vipleiloes.com.br','www.vipleiloes.com.br')
                and vip_detail_url(row['source_url']) is not None)
    if org=='Detran MG':
        from mg_detran_collect import detail_identity
        return (not row.get('event_url')
                and row.get('source_link_type')=='event'
                and row.get('source_type')=='state'
                and row.get('date_kind')=='closing'
                and detail_identity(row.get('source_url')) is not None
                and bool(re.fullmatch(r"\d{1,6}/20\d{2}",row.get('auction_number') or "")))
    if org in ("Vardana Leilões","Claudio Kuss Leilões"):
        from regional_collect import strict_url
        site = "vardana" if org=="Vardana Leilões" else "claudio"
        return (not row.get("event_url") and row.get("source_type")=="private"
                and row.get("source_link_type")=="event"
                and row.get("state")=="PR" and strict_url(site,row.get("source_url")))
    if org=="Bolsa de Leilões":
        from bolsa_collect import detail_id
        return (not row.get("event_url") and row.get("source_type")=="private"
                and row.get("source_link_type")=="event"
                and detail_id(row.get("source_url")) is not None)
    if org=='Leilo':
        from leilo_collect import event_slug
        slug=event_slug(row.get("source_url"))
        key=row.get("event_id") or row.get("id") or ""
        date=row.get("auction_date") or ""
        hour=(row.get("auction_time") or "").replace(":","")
        return (bool(slug) and not row.get("event_url")
                and row.get("source_type")=="private"
                and row.get("source_link_type")=="event"
                and key==f"leilo-{slug}-{date}-{hour}")
    if org in ("Parque dos Leilões","Flex Leilões","Hisa Leilões"):
        from secondary_collect import trusted_url
        adapter={"Parque dos Leilões":"parque","Flex Leilões":"flex",
                 "Hisa Leilões":"hisa"}[org]
        return (not row.get("event_url") and row.get("source_type")=="private"
                and row.get("source_link_type")=="event"
                and trusted_url(adapter,row.get("source_url")))
    if org=="PMKLog":
        from pmklog_collect import event_id
        key=event_id(row.get("source_url"))
        return (key is not None and row.get("event_id")==
                f"pmklog-{key[1]}-{row.get('auction_date')}" and
                not row.get("event_url") and
                row.get("source_link_type")=="event" and
                row.get("source_type")=="private")
    if org=="Palácio dos Leilões":
        from palacio_collect import auction_id
        aid=auction_id(row.get("source_url"))
        return (aid is not None and row.get("event_id")==
                f"palacio-{aid}-{row.get('auction_date')}" and
                not row.get("event_url") and
                row.get("source_link_type")=="event" and
                row.get("source_type")=="private")
    if org=='Freitas Leiloeiro':
        from freitas_collect import official_id
        return not row.get('event_url') and official_id(row['source_url']) is not None
    approved=APPROVED_CURATED.get(row.get('id'))
    if approved is None: return False
    source_host,direct,approved_org,approved_date=approved
    return (original.hostname==source_host and row.get('event_url')==direct
            and row.get('organizer')==approved_org
            and row.get('auction_date')==approved_date)

"""Conservative allowlist for auction destinations.

HTTPS and a government article alone do not prove an auction is legitimate.
Only exact known hosts and event-specific URL forms can be published.
Any new platform requires a manual source/registrar review and a code change.
"""
import re
from urllib.parse import urlsplit, parse_qs

def destination_status(row):
    url = row.get("event_url") or (row.get("source_url") if row.get("source_link_type") == "event" or row.get("organizer") == "Freitas Leiloeiro" else None)
    if not isinstance(url, str):
        return False, "missing direct auction destination"
    try:
        p = urlsplit(url)
        host = (p.hostname or "").lower()
        if p.scheme != "https" or not host or p.username or p.password or p.port not in (None, 443):
            return False, "invalid https destination"
        if p.fragment or "\\" in url or re.search(r"[\x00-\x20\x7f]", url):
            return False, "unsafe destination characters"
        path = p.path.rstrip("/")
        if host in ("www.vipleiloes.com.br", "vipleiloes.com.br"):
            ok = bool(re.fullmatch(r"/evento/detalhes/[a-zA-Z0-9_-]+", path)) and row.get("organizer") == "VIP Leilões"
        elif host in ("www.copart.com.br", "copart.com.br"):
            ok = bool(re.fullmatch(r"/saleListResult/\d+/\d{4}-\d{2}-\d{2}", path)) and row.get("organizer") == "Copart" and row.get("auction_date") == path.rsplit("/", 1)[-1]
        elif host in ("www.freitasleiloeiro.com.br", "freitasleiloeiro.com.br"):
            q = parse_qs(p.query, strict_parsing=True)
            ok = path.lower() == "/leiloes/lotes" and len(q) == 1 and len(q.get("leilaoId", [])) == 1 and q["leilaoId"][0].isdigit() and row.get("organizer") == "Freitas Leiloeiro"
        elif host == "leilao.transito.mg.gov.br":
            from mg_detran_collect import detail_identity
            ok = (row.get("organizer") == "Detran MG" and
                  row.get("source_type") == "state" and
                  row.get("date_kind") == "closing" and
                  detail_identity(url) is not None and
                  row.get("source_link_type") == "event")
        elif host in ("vardanaleiloes.com.br","www.vardanaleiloes.com.br",
                      "claudiokussleiloes.com.br","www.claudiokussleiloes.com.br"):
            from regional_collect import strict_url
            site = ("vardana" if row.get("organizer")=="Vardana Leilões" else
                    "claudio" if row.get("organizer")=="Claudio Kuss Leilões" else None)
            ok = bool(site and strict_url(site,url) and
                      row.get("source_link_type")=="event" and
                      row.get("source_type")=="private" and
                      row.get("state")=="PR" and not row.get("event_url"))
        elif host in ("www.bolsadeleiloes.com.br","bolsadeleiloes.com.br"):
            from bolsa_collect import detail_id
            ok = (row.get("organizer")=="Bolsa de Leilões" and
                  row.get("source_type")=="private" and
                  row.get("source_link_type")=="event" and
                  not row.get("event_url") and
                  detail_id(url) is not None)
        elif host in ("leilo.com.br","www.leilo.com.br"):
            from leilo_collect import event_slug
            ok=bool(row.get("organizer")=="Leilo" and
                    row.get("source_type")=="private" and
                    row.get("source_link_type")=="event" and
                    not row.get("event_url") and event_slug(url))
        elif host in ("parquedosleiloes.com.br","www.parquedosleiloes.com.br",
                      "flexleiloes.com.br","www.flexleiloes.com.br",
                      "hisaleiloes.com.br","www.hisaleiloes.com.br"):
            from secondary_collect import trusted_url
            org=row.get("organizer")
            key={"Parque dos Leilões":"parque","Flex Leilões":"flex",
                 "Hisa Leilões":"hisa"}.get(org)
            ok=bool(key and trusted_url(key,url) and
                    row.get("source_link_type")=="event" and
                    row.get("source_type")=="private" and not row.get("event_url"))
        elif host in ("rogeriomenezes.com.br","www.rogeriomenezes.com.br"):
            from rogerio_collect import detail_id
            ok=bool(row.get("organizer")=="Rogério Menezes" and
                    row.get("source_type")=="private" and
                    row.get("source_link_type")=="event" and
                    not row.get("event_url") and detail_id(url))
        elif host in ("loopleiloes.com.br","www.loopleiloes.com.br"):
            from loop_collect import event_id
            ok=bool(row.get("organizer")=="Loop Leilões" and
                    row.get("source_type")=="private" and
                    row.get("source_link_type")=="event" and
                    not row.get("event_url") and event_id(url))
        elif host in ("pmklog.com.br", "www.pmklog.com.br"):
            if row.get("organizer")=="PMKLog":
                from pmklog_collect import event_id
                ok=bool(event_id(url) and row.get("source_link_type")=="event"
                        and row.get("source_type")=="private" and
                        not row.get("event_url"))
            else:
                # Curated Detran-GO events have an independently approved
                # official notice and exact-edition URL.
                q = parse_qs(p.query)
                ok = path == "/leilao/evento/leilao-detran" and len(q.get("evento", [])) == 1 and bool(re.fullmatch(r"[a-fA-F0-9-]{36}", q["evento"][0])) and bool(row.get("event_url"))
        elif host in ("palaciodosleiloes.com.br","www.palaciodosleiloes.com.br"):
            from palacio_collect import auction_id
            ok=bool(row.get("organizer")=="Palácio dos Leilões" and
                    row.get("source_type")=="private" and
                    row.get("source_link_type")=="event" and
                    not row.get("event_url") and auction_id(url))
        elif host in ("www.focoleiloes.com.br", "focoleiloes.com.br"):
            ok = bool(re.fullmatch(r"/leilao/\d+/lotes", path)) and bool(row.get("event_url")) and row.get("source_type") in ("municipal", "state", "federal")
        elif host == "exchange.superbid.net":
            ok = bool(re.fullmatch(r"/evento/[a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_-]+)*", path)) and row.get("organizer") in ("Superbid", "Superbid Exchange")
        else:
            ok = False
        return (True, "known event-specific route; identity requires operational review") if ok else (False, "unknown platform or non-event URL")
    except (ValueError, AttributeError):
        return False, "malformed destination"

def certify_links(rows):
    """Attach a conservative structural classification after source collection.

    Platform adapters verify the underlying listing; curated event_url fields
    must be manually registered against the government notice before use.
    """
    for row in rows:
        ok, reason = destination_status(row)
        row["link_verified"] = bool(ok)
        row["link_review"] = "trusted_route" if ok else "quarantine"
        if not ok:
            row["link_review_reason"] = reason
    return rows

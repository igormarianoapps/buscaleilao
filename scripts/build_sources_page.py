"""Build an honest directory of all nominated auction platforms."""
import html,json
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
TITLES={1:"Goiás e Distrito Federal",2:"São Paulo",3:"Paraná, Minas Gerais e Rio de Janeiro",4:"Integrações existentes"}
def approved_count(site,events):
    keys=set()
    for e in events:
        try:host=urlsplit(e.get("event_url") or e.get("source_url") or "").hostname
        except ValueError:host=None
        if host in site.get("allowed_hosts",[]) and e.get("link_verified") is True and e.get("destination_verified") is True:
            keys.add((e.get("organizer"),e.get("event_id") or e.get("id")))
    return len(keys)
def render(sites,diag=None,events=None):
    diag=(diag or {}).get("platforms",{})
    events=events or []
    body=[]
    for batch,name in TITLES.items():
        body.append('<section><h2>'+html.escape(name)+'</h2><div class="cards">')
        for site in (s for s in sites if s.get("batch")==batch):
            url=site.get("discovery_url","")
            parts=urlsplit(url)
            if parts.scheme!="https" or parts.hostname not in site.get("allowed_hosts",[]) or parts.username or parts.password:
                continue
            count=approved_count(site,events)
            condition=diag.get(site["id"],{}).get("status")
            status=(f"{count} leilão(ões) confirmado(s)" if count else
                "Monitorado, sem eventos confirmados" if condition=="reachable" else
                "Acesso à coleta indisponível" if condition=="unreachable" else
                "Aguardando diagnóstico")
            body.append('<article class="source"><h3>'+html.escape(site["name"])+
              '</h3><p>'+html.escape(parts.hostname)+'</p><small>'+html.escape(status)+
              '</small><a href="'+html.escape(url,quote=True)+
              '" target="_blank" rel="noopener noreferrer">Abrir site da fonte</a></article>')
        body.append("</div></section>")
    return '''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Fontes monitoradas — BuscaLeilão</title>
<style>:root{font-family:Inter,Arial,sans-serif;color:#172236;background:#f5f7fa}*{box-sizing:border-box}body{margin:0}
header{background:#fff;border-bottom:1px solid #e5e9ef;padding:20px max(20px,calc((100% - 1024px)/2));display:flex;justify-content:space-between;gap:18px}
.logo{font-size:22px;font-weight:800;color:#1749b3}a{color:#1749b3}
main{max-width:1024px;margin:42px auto;padding:0 20px}.intro{line-height:1.6;color:#52627a}
section{margin:30px 0}h2{font-size:21px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}
.source{background:#fff;border:1px solid #e5e9ef;border-radius:12px;padding:18px;display:grid;gap:8px}
.source h3{margin:0;font-size:17px}.source p{font-size:13px;color:#52627a;margin:0}
.source small{font-size:12px;background:#edf2f7;padding:8px;border-radius:6px}.source a{font-weight:700;font-size:14px}
:focus-visible{outline:3px solid #1749b3;outline-offset:2px}</style></head><body>
<header><span class="logo">BuscaLeilão</span><a href="/">Voltar à agenda</a></header>
<main><h1>Fontes de leilões monitoradas</h1>
<p class="intro">Acompanhamos os sites abaixo. <b>Uma fonte monitorada não significa um leilão validado.</b>
Somente eventos com data confirmada e link individual aprovado aparecem na agenda. A disponibilidade
de um domínio não comprova a habilitação do leiloeiro: confira os órgãos oficiais antes de participar.</p>
'''+''.join(body)+'''<p class="intro">Os sites podem realizar eventos em outros estados além da região de referência.
O monitoramento não constitui certificação ou endosso das empresas.</p></main></body></html>'''
def main():
    def load(name,default):
        try:return json.loads((ROOT/"app"/name).read_text(encoding="utf-8"))
        except (OSError,ValueError):return default
    sites=load("auction-platforms.json",[])
    diag=load("auction-platform-diagnostics.json",{})
    feed=load("events.json",{})
    (ROOT/"app/fontes.html").write_text(render(sites,diag,feed.get("events",[]))+"\n",encoding="utf-8")
    print("Built monitoring directory:",len(sites),"platforms")
if __name__=="__main__":main()

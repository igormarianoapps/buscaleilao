"""GitHub Actions run summary for MVP readiness.

This only reports what was observed in the current run. It never promotes
research leads to events or marks the release gate as passed.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"app"

def read_current(name, checked_at):
    path=ROOT/name
    try:
        obj=json.loads(path.read_text(encoding="utf-8"))
        stamp=datetime.fromisoformat(str(obj.get("checked_at","")).replace("Z","+00:00"))
        source=datetime.fromisoformat(checked_at.replace("Z","+00:00"))
        if stamp.tzinfo is None or source.tzinfo is None:
            return None
        if abs(stamp-source)>timedelta(minutes=35):
            return None
        return obj
    except (OSError,ValueError,TypeError,AttributeError):
        return None

def summarize(report,pncp=None,review=None,vip=None):
    if not isinstance(report,dict) or not report.get("checked_at"):
        return "## BuscaLeilão — MVP\n\nNão foi possível ler o relatório da coleta.\n"
    lines=["## BuscaLeilão — coleta do MVP",
           f"- Relatório de coleta: \`{report['checked_at']}\`",
           f"- Eventos únicos: **{report.get('unique_events','?')}**",
           f"- UFs com eventos: **{len(report.get('states_with_events',[]))}/27**",
           f"- Fontes curadas aprovadas: **{report.get('curated_success','?')}**",
           f"- Fontes curadas com falha: **{report.get('curated_failure','?')}**",
           f"- Links diretos: **{report.get('direct_event_links','?')}**",
           f"- Links genéricos de calendários: **{report.get('calendar_links','?')}**",
           f"- PNCP: **{'não produzido nesta coleta' if pncp is None else str(pncp.get('count',0))+' candidatos; '+str(len(pncp.get('errors',[])))+' erros de consulta'}**",
           f"- Revisão PNCP/RSS: **{'não produzida nesta coleta' if review is None else str(review.get('unverified_count',0))+' pistas, '+str(review.get('pncp_leads',0))+' do PNCP'}**",
           f"- VIP DOM: **{'sem diagnóstico novo; confirmar log do coletor' if vip is None else str(vip.get('status','desconhecido'))+'; '+str(vip.get('candidate_cards','?'))+' cartões'}**",
           "",
           "**Critério P0.1:** conferir no GitHub Actions a conclusão de todas as etapas, inclusive publicação. Este resumo não comprova sozinho a conclusão do workflow.",
           "**Critério P0.2:** são necessárias três execuções completas consecutivas com sucesso; testes isolados não contam."]
    if report.get("failed"):
        lines+=["","### Fontes com falha"]
        for item in report["failed"][:25]:
            lines.append(f"- \`{item.get('id','?')}\`: {str(item.get('error','?'))[:170]}")
    return "\n".join(lines)+"\n"

def main():
    try:
        report=json.loads((ROOT/"collection-report.json").read_text(encoding="utf-8"))
        stamp=report["checked_at"]
        checked=datetime.fromisoformat(stamp.replace("Z","+00:00"))
        now=datetime.now(timezone.utc)
        if checked.tzinfo is None or not (timedelta(0) <= now-checked <= timedelta(hours=2)):
            summary=("## BuscaLeilão — execução sem coleta nova\n\n"
                     "O relatório encontrado é de uma execução anterior. "
                     "**Não contar esta execução para P0.1/P0.2.**\n")
        else:
            summary=summarize(report,
                read_current("pncp-candidates.json",stamp),
                read_current("review-queue.json",stamp),
                read_current("vip-dom-diagnostics.json",stamp))
    except (OSError,ValueError,TypeError,KeyError,AttributeError):
        summary=("## BuscaLeilão — execução sem coleta validada\n\n"
                 "O relatório atual não está disponível ou está inválido. "
                 "**Não contar esta execução para P0.1/P0.2.**\\n")
    print(summary)
    target=os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with open(target,"a",encoding="utf-8") as file:
            file.write(summary)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""lens/lens_map — визуальная карта нарушений канона (одна линза из fan-out).

Вход:  текстовый файл + нарушения — JSON от `canon-lens check --json` (--violations)
       ИЛИ канон-файл, тогда проверку запускаем сами (--canon).
Выход: один самодостаточный HTML: текст с подсвеченными спанами + панель правил
       по пунктам канона, клик по пункту подсвечивает место. Без внешних зависимостей.

    python canon-lens/lens/lens_map.py draft.md --canon canon-lens/canon.sostav.md -o map.html
    canon-lens check draft.md --json > v.json && python canon-lens/lens/lens_map.py draft.md --violations v.json
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))   # canon-lens/ → import canon_lens при --canon


def _collect(text_path: Path, args) -> dict:
    if args.violations:
        return json.loads(Path(args.violations).read_text(encoding="utf-8"))
    from canon_lens.rules import load_canon
    from canon_lens.check import check_text, summary
    vs = check_text(text_path.read_text(encoding="utf-8"), load_canon(args.canon))
    return {"file": str(text_path), "summary": summary(vs),
            "violations": [v.as_dict() for v in vs]}


def _vid(v: dict) -> str:
    return f'{v["rule"]}@{v["offset"][0]}-{v["offset"][1]}'


def _render_text(text: str, violations: list[dict]) -> str:
    inline = [v for v in violations if v["offset"][1] > v["offset"][0]]
    cuts = sorted({0, len(text)}
                  | {v["offset"][0] for v in inline}
                  | {v["offset"][1] for v in inline})
    out = []
    for a, b in zip(cuts, cuts[1:]):
        seg = html.escape(text[a:b])
        cover = [v for v in inline if v["offset"][0] <= a and v["offset"][1] >= b]
        if not cover:
            out.append(seg)
            continue
        if any(v["category"] == "redaction" for v in cover):
            cls = "cat-redaction"
        elif any(v["severity"] == "error" for v in cover):
            cls = "sev-error"
        else:
            cls = "sev-warning"
        vids = " ".join(_vid(v) for v in cover)
        tip = " · ".join(v["message"] for v in cover)
        out.append(f'<span class="v {cls}" data-vids="{html.escape(vids)}" '
                   f'title="{html.escape(tip)}">{seg}</span>')
    return "".join(out)


def _render_panel(violations: list[dict]) -> str:
    if not violations:
        return ('<section><h3>канон</h3><p style="color:#3a7a3a;padding:6px 9px">'
                'нарушений нет — черновик проходит канон</p></section>')
    by_pt: dict[int, list] = {}
    for v in violations:
        by_pt.setdefault(v["point"], []).append(v)
    blocks = []
    for pt in sorted(by_pt):
        head = f"п.{pt} канона" if pt else "редакция · безопасность публикации"
        items = []
        for v in by_pt[pt]:
            inline = v["offset"][1] > v["offset"][0]
            loc = f'{v["line"]}:{v["col"]}' if inline else "—"
            sev = "cat-redaction" if v["category"] == "redaction" else f'sev-{v["severity"]}'
            fix = (f'<div class="fix">→ {html.escape(v["fix"])}</div>'
                   if v.get("fix") else "")
            items.append(
                f'<li class="{sev}" data-vid="{html.escape(_vid(v))}">'
                f'<span class="loc">{loc}</span> '
                f'<b>«{html.escape(v["quote"])}»</b> {html.escape(v["message"])}{fix}</li>')
        blocks.append(f'<section><h3>{html.escape(head)}</h3>'
                      f'<ul>{"".join(items)}</ul></section>')
    return "".join(blocks)


_TPL = """<!doctype html><meta charset="utf-8">
<title>canon-lens · карта нарушений · __NAME__</title>
<style>
 :root{--err:#d64545;--errbg:#fdecec;--warn:#b7791f;--warnbg:#fdf6e3;--red:#7c3aed;--redbg:#f3ecfd}
 *{box-sizing:border-box}
 body{margin:0;font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:#1a1a1a;background:#fafafa}
 header{padding:12px 20px;border-bottom:1px solid #e2e2e2;background:#fff}
 header h1{margin:0;font-size:14px;font-weight:600}
 header code{background:#f0f0f0;padding:1px 5px;border-radius:4px}
 .sum{margin-top:4px;color:#555;font-size:13px}
 .sum b.e{color:var(--err)} .sum b.w{color:var(--warn)}
 .wrap{display:grid;grid-template-columns:1fr 400px;height:calc(100vh - 56px)}
 .doc{padding:22px 26px;overflow:auto;white-space:pre-wrap;word-wrap:break-word;background:#fff;border-right:1px solid #e2e2e2;font:13px/1.75 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
 .panel{overflow:auto;padding:12px 16px}
 .panel section{margin-bottom:14px}
 .panel h3{margin:0 0 6px;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#888}
 .panel ul{list-style:none;margin:0;padding:0}
 .panel li{padding:6px 9px;border-radius:6px;margin-bottom:4px;cursor:pointer;border-left:3px solid #ccc;background:#fff}
 .panel li:hover{filter:brightness(.97)}
 .panel li .loc{color:#999;font-variant-numeric:tabular-nums;margin-right:5px;font-family:ui-monospace,monospace;font-size:12px}
 .panel li .fix{color:#555;font-size:12px;margin-top:3px}
 .v{border-radius:3px;padding:0 1px}
 .sev-error,li.sev-error{background:var(--errbg);border-color:var(--err)}
 .sev-warning,li.sev-warning{background:var(--warnbg);border-color:var(--warn)}
 .cat-redaction,li.cat-redaction{background:var(--redbg);border-color:var(--red)}
 .v.flash{outline:2px solid #111;outline-offset:1px}
</style>
<header>
 <h1>canon-lens · карта нарушений · <code>__NAME__</code></h1>
 <div class="sum">__SUMLINE__</div>
</header>
<div class="wrap">
 <div class="doc" id="doc">__BODY__</div>
 <div class="panel">__PANEL__</div>
</div>
<script>
 document.querySelectorAll('.panel li').forEach(function(li){
   li.addEventListener('click', function(){
     var id = li.dataset.vid;
     document.querySelectorAll('.v.flash').forEach(function(e){ e.classList.remove('flash'); });
     var t = [].slice.call(document.querySelectorAll('.v')).filter(function(e){
       return e.dataset.vids.split(' ').indexOf(id) !== -1;
     });
     if (t.length){
       t.forEach(function(e){ e.classList.add('flash'); });
       t[0].scrollIntoView({block:'center', behavior:'smooth'});
     }
   });
 });
</script>
"""


def build_html(text: str, data: dict) -> str:
    s = data["summary"]
    sumline = (f'{s["total"]} нарушений: <b class="e">{s["errors"]} error</b>, '
               f'<b class="w">{s["warnings"]} warning</b> &nbsp;·&nbsp; '
               f'пункты {s["points"]} &nbsp;·&nbsp; '
               + ("чисто по error" if s["clean"] else "есть error"))
    return (_TPL
            .replace("__NAME__", html.escape(Path(data["file"]).name))
            .replace("__SUMLINE__", sumline)
            .replace("__BODY__", _render_text(text, data["violations"]))
            .replace("__PANEL__", _render_panel(data["violations"])))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="lens_map", description="визуальная карта нарушений канона")
    p.add_argument("file")
    p.add_argument("--canon", help="канон-файл (запустить проверку самому)")
    p.add_argument("--violations", help="JSON от `canon-lens check --json`")
    p.add_argument("-o", "--out", default="canon-map.html")
    a = p.parse_args(argv)
    if not a.canon and not a.violations:
        p.error("нужен --canon или --violations")

    tp = Path(a.file)
    data = _collect(tp, a)
    out = build_html(tp.read_text(encoding="utf-8"), data)
    Path(a.out).write_text(out, encoding="utf-8")
    print(f"{a.out}  ({len(out)} b, {data['summary']['total']} нарушений)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

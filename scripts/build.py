#!/usr/bin/env python3
"""
Render the site from data/*.json into dist/.

    python scripts/build.py

Data is the source of truth. Nothing about a deal is written in this file;
edit the JSON and rebuild.
"""

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DIST = ROOT / "dist"

FLAG = {
    "disclosed": ("f-disc", "Disclosed"),
    "reported": ("f-est", "Reported"),
    "confidential": ("f-conf", "Confidential"),
    "unverified": ("f-unv", "Unverified"),
}
ORIGIN = {"qc": "o-qc", "roc": "o-roc", "us": "o-us"}


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def sub(text):
    return f'<div class="sub">{text}</div>' if text else ""


def deal_row(d):
    cls, label = FLAG.get(d["confidence"], FLAG["confidential"])
    src = (
        f'<a class="src" href="{d["source"]}" target="_blank" rel="noopener">source</a>'
        if d.get("source") else '<span class="src none">no link</span>'
    )
    scls = "s-" + d["sector"] if d["sector"] in ("energy", "digital") else ""
    return f"""          <tr data-o="{d['origin']}" data-p="{d['year']}" data-s="{d['sector']}">
            <td><div class="asset">{d['asset']}</div>{sub(d.get('asset_note'))}</td>
            <td><span class="sect {scls}">{d['sector_label']}</span></td>
            <td>{d['acquirer']}{sub(d.get('acquirer_note'))}</td>
            <td><span class="origin {ORIGIN.get(d['origin'],'o-qc')}">{d['origin_label']}</span></td>
            <td class="num">{d['value']}{sub(d.get('value_note'))}</td>
            <td>{d['structure']}{sub(d.get('structure_note'))}</td>
            <td class="num">{d['date']}{sub(d.get('date_note'))}</td>
            <td><span class="flag {cls}">{label}</span><div class="sub">{src}</div></td>
          </tr>"""


def pipe_card(p):
    return f"""      <div class="pcard">
        <h3>{p['name']}</h3><div class="mw">{p['headline']}</div>
        <div class="sub">{p['sub']}</div>
        <p>{p['body']}</p>
        <div class="date">{p['status']}</div>
      </div>"""


def log_row(e, today):
    age = (date.fromisoformat(today) - date.fromisoformat(e["date"])).days
    d = date.fromisoformat(e["date"]).strftime("%d %b %Y")
    return f"""      <div class="logrow" data-age="{age}">
        <div class="logdate">{d}</div><div class="logkind">{e['kind']}</div>
        <div class="logtext">{e['text']}</div>
      </div>"""


def note_block(n, last):
    ps = "".join(f"<p>{p}</p>" for p in n["paragraphs"])
    style = "" if last else ' style="margin-bottom:26px"'
    return f"""    <div class="note"{style}>
      <div class="meta">{n['number']} · {n['date']}</div>
      <h3>{n['title']}</h3>
      {ps}
    </div>"""


def main():
    deals, pipeline = load("deals.json"), load("pipeline.json")
    notes, changelog = load("notes.json"), load("changelog.json")
    today = date.today().isoformat()
    stamp = date.today().strftime("%d %b %Y")

    years = sorted({d["year"] for d in deals}, reverse=True)
    year_chips = "\n        ".join(
        f'<button class="chip" data-g="p" data-v="{y}" aria-pressed="false">{y}</button>'
        for y in years
    )

    disclosed = sum(1 for d in deals if d["confidence"] == "disclosed")
    linked = sum(1 for d in deals if d.get("source"))

    html = (ROOT / "template.html").read_text(encoding="utf-8")
    html = (html
        .replace("{{STAMP}}", f"Collection runs daily · last build {stamp} · {len(deals)} transactions · {len(pipeline)} pipeline entries")
        .replace("{{YEAR_CHIPS}}", year_chips)
        .replace("{{ROWS}}", "\n".join(deal_row(d) for d in deals))
        .replace("{{PIPELINE}}", "\n".join(pipe_card(p) for p in pipeline))
        .replace("{{CHANGELOG}}", "\n".join(log_row(e, today) for e in changelog))
        .replace("{{NOTES}}", "\n".join(
            note_block(n, i == len(notes) - 1) for i, n in enumerate(notes)))
        .replace("{{N_DEALS}}", str(len(deals)))
        .replace("{{N_DISCLOSED}}", str(disclosed))
        .replace("{{PCT_LINKED}}", f"{round(100 * linked / len(deals))}%")
    )

    DIST.mkdir(exist_ok=True)
    (DIST / "index.html").write_text(html, encoding="utf-8")
    print(f"built dist/index.html — {len(deals)} deals, {disclosed} disclosed, {linked} linked")


if __name__ == "__main__":
    main()

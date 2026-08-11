# Quebec Capital Tracker

Deal-level intelligence on Quebec energy, infrastructure and mid-market
transactions, built by reading French-language primary sources — Régie de
l'énergie dockets, Hydro-Québec releases, issuer filings — and publishing them
as structured English.

Every figure carries its source and a confidence flag. Where a number is
sealed, the tracker says so instead of estimating.

## How it works

```
sources.yaml ──> scripts/collect.py ──> data/review-queue.json
                                              │
                                    (you read and verify)
                                              │
                                              v
                                       data/deals.json
                                              │
                        scripts/build.py ─────┴──> dist/index.html
```

Three data files hold everything the site shows: `deals.json`,
`pipeline.json`, `notes.json`, plus `changelog.json` for the edit history.
Nothing about a transaction lives in the template. Edit the JSON, rebuild.

**The collector never writes to `deals.json`.** It finds candidates and puts
them in a queue. You open the source, confirm the figures, and move the entry
across yourself. That boundary is deliberate: an extraction error that
publishes itself costs more than a day of delay, and the whole value of this
tracker is that its numbers hold up when someone checks them.

## Setup

```bash
git clone https://github.com/YOURNAME/quebec-capital-tracker
cd quebec-capital-tracker
pip install -r requirements.txt
python scripts/build.py
open dist/index.html
```

## Deploying

**GitHub Pages** — push to `main`. The `deploy` workflow builds and publishes.
Enable it once under Settings → Pages → Source: GitHub Actions.

**Vercel** — import the repo. `vercel.json` already declares the build command
and output directory. Add a custom domain there when you want one.

Either way the site rebuilds on every push, so updating a number is a commit.

## The daily loop

`.github/workflows/collect.yml` runs the scan every weekday at 07:00 Toronto
time. When it finds something it commits the queue and opens an issue listing
what turned up. Your morning job:

1. Open the issue.
2. Read each linked release at the source. Not the headline — the release.
3. Move what belongs into `data/deals.json`, with `source` and `retrieved` filled in.
4. Add a line to `data/changelog.json` saying what you did and why.
5. Commit. The site redeploys.

Log corrections and downgrades too, not just additions. The change history is
the part that makes the numbers credible.

## Sources

Registered in `sources.yaml` with the method that actually works for each.

| Source | Method | Why it matters |
|---|---|---|
| Hydro-Québec | RSS | Bond issues with amount, coupon, price, yield, maturity, full syndicate |
| Énergir | HTML | Every private placement with the amount, archived to 2017 |
| Boralex | HTML | Quebec project financings and the Brookfield/La Caisse arrangement |
| La Caisse | HTML | Quebec infrastructure and mid-market positions |
| Novacap | HTML | Mid-market add-ons and exits — mostly outbound US, filter hard |
| Innergex | manual | Script-rendered; archive pruned after the CDPQ take-private |
| Canada Infrastructure Bank | manual | Script-rendered; loan terms privileged under s.28 of the CIB Act |
| SEDAR+ | manual | Session-gated, and automated access is against its terms |
| Régie de l'énergie | manual | French PDFs; per-developer PPA pricing is filed under seal |

The manual entries are listed on purpose. A source you cannot automate is
still a source, and leaving it out of the registry means forgetting it exists.

Northland Power was scanned and cut — its recent output is Poland and Taiwan
offshore wind, outside scope.

## Confidence flags

| Flag | Meaning |
|---|---|
| `disclosed` | Stated by a party or a regulator |
| `reported` | Credible secondary press, not yet confirmed in a filing |
| `confidential` | The figure exists but is sealed |
| `unverified` | Carried from secondary reporting, not yet confirmed in a primary document |

`unverified` is shown on the site rather than hidden. A visible gap is worth
more than a number you cannot defend.

## What this deliberately does not capture

Per-developer PPA pricing, debt tranche margins, mezzanine terms and
mid-market multiples are sealed or redacted in Quebec filings. They are marked
confidential rather than estimated.

## Adding a transaction

```json
{
  "id": "short-slug",
  "asset": "Name",
  "asset_note": "One line of context",
  "acquirer": "Buyer or arranger",
  "acquirer_note": "Structure detail",
  "origin": "qc | roc | us",
  "origin_label": "Quebec",
  "value": "C$000M",
  "value_note": "Multiple or per-share",
  "structure": "Take-private | Secured debt | ...",
  "structure_note": "Coupon, premium, pricing",
  "date": "7 Aug 2026",
  "date_note": "Closing detail",
  "year": "2026",
  "confidence": "disclosed",
  "source": "https://...",
  "retrieved": "2026-08-10"
}
```

Year filters are generated from the data, so a new year appears on its own.

---

Independent research. Not investment advice. Verify against primary sources.

# Data Provider Research (Phase 0)

Status: living document. Pricing/coverage claims below are sourced from provider
marketing pages and third-party comparison blogs found via web search in
September 2026 (links in **Sources**), **not** verified against a signed
contract. Before any commercial commitment, re-verify current pricing and
terms directly with the vendor — betting-data pricing pages change often and
review sites are frequently sponsored by the vendor they rank first.

No API keys, credentials, or paid contracts exist yet. Nothing in this
repository talks to a live paid provider. This document exists to decide
which ones we *would* integrate with, and in what order.

## 1. Evaluation framework

Every candidate is scored on the same criteria, because "best API" without
criteria is meaningless for a system whose credibility depends on data
quality:

| Criterion | Why it matters here |
|---|---|
| Coverage (leagues/seasons) | Backtesting needs many leagues × many seasons to be statistically meaningful |
| Historical depth | Walk-forward validation (Section 13 of the brief) needs years of history, not just "today's fixtures" |
| xG / advanced stats | Poisson/Dixon-Coles and ML features depend on shot quality, not just goals |
| Odds coverage (pre-match + historical + closing line) | Required for the Market Edge Engine and CLV analysis |
| Update latency / freshness | Live lineups, injuries, odds movement need near-real-time feeds |
| License & commercial-use terms | A provider that forbids commercial redistribution is unusable for a product, however good the data is |
| Price & rate limits | Determines which tier funds Phase 2 (data ingestion) vs. later phases |
| Integration ease | REST + documented schema vs. scraping-only |

**Absolute rule applied here:** we do not scrape or use any source whose
Terms of Service forbid the derivative commercial use we intend (a
prediction/edge product). Where a source is scraping-only and ToS-ambiguous
(FBref, Understat, OddsPortal), it is scoped to **research/model-prototyping
use only**, never as a production ingestion path, until we have a licensed
replacement.

## 2. Match / team results + basic stats

| Provider | Coverage | History | Price (entry) | License notes |
|---|---|---|---|---|
| **football-data.org** | 12 major competitions free (PL, La Liga, Bundesliga, Serie A, Ligue 1, UCL, etc.) | Free tier: recent seasons only, delayed; paid tiers extend history | Free tier: 10 req/min, no lineups/stats. Paid tiers add competitions, lower delay, more calls | Attribution required on free tier; commercial use needs a paid plan per their pricing page |
| **API-Football (API-SPORTS)** | Very broad (1000+ leagues claimed) | Multi-season | Pro tier from ~$19/mo (daily-request-cap model) | Commercial use allowed on paid plans; cheap for prototyping, but request-cap model is awkward for large historical backfills |
| **Sportmonks Football API** | 2,200+ leagues/cups, uniform schema across leagues | Multi-season, varies by plan | From €29/mo; xG and odds are paid add-ons (xG basic €19–99/mo, xG advanced €199–399/mo) | Explicit commercial licensing, REST + webhooks, best documentation of the low/mid tier options |
| **Football-Data.co.uk** | ~20+ European leagues | Full match results + odds from 15+ bookmakers, season 2000/01 → present | **Free**, plain CSV | No formal commercial API/ToS — historically used widely in academic and hobbyist betting-model research. Good for **backtesting datasets**, not a live production feed. Re-check current terms before commercial use. |

**Assessment:** football-data.org's free tier is fine for early prototyping
against major leagues but is too thin (no lineups, no shot stats, delayed) to
be the backbone. Between API-Football and Sportmonks, **Sportmonks** has the
stronger case for the paid/production ingestion path (uniform schema across
leagues is a big engineering win — one normalization layer instead of one per
league quirk), with API-Football kept as a **cheap secondary/cross-check
source** for the discrepancy checks Section 8 of the brief asks for
("consensus between models" partly comes from consensus between *data*
sources too). **Football-Data.co.uk stays as the historical backtesting
seed dataset** for Phase 5–7 because it already bundles results + closing
odds for 20+ years, which is exactly the walk-forward corpus Section 13
needs, without spending the paid-API budget before we've proven a model has
edge at all.

## 3. Expected Goals (xG) and advanced event data

| Provider | What it offers | Access | Commercial use |
|---|---|---|---|
| **StatsBomb Open Data** | Full event-level data (incl. xG) for select free competitions (women's football, some historical men's seasons, some internationals) | Public GitHub repo, free | Free tier explicitly scoped to **research/personal analysis**, not commercial redistribution — StatsBomb sells enterprise licenses for that |
| **StatsBomb / Opta (Stats Perform) / Wyscout (Hudl) commercial data** | Industry-standard event data & xG models, the actual data feeding most professional clubs' analytics | Enterprise sales, no public self-serve pricing | Full commercial license available, but priced and negotiated per deal — out of reach for Phase 0–7 bootstrap budget |
| **Understat** | Free xG per shot/match/team via public JSON embedded in pages, 6 top European leagues since 2014/15 | No official API — third-party scraper libraries exist (e.g. `understatAPI`) | No published commercial-use terms; **treat as research-only**, not a production data path |
| **FBref** | Advanced stats including xG (sourced from Opta/StatsBomb depending on competition) via scraping | Scraping only | Same caveat as Understat — research-only |
| **Sportmonks xG add-on** | xG figures bundled into the same uniform API | Paid add-on on top of base plan | Commercially licensed, same vendor as Section 2 |

**Assessment:** the only xG source with a clean commercial license at a
budget we can justify before the product proves itself is **Sportmonks' xG
add-on**. Understat/FBref are used only to **prototype and validate xG-based
features offline** (Phase 4–6 experimentation) — never wired into the live
ingestion pipeline that feeds real predictions, to avoid building the product
on a foundation we'd have to rip out for legal reasons the moment it matters.

## 4. Lineups, injuries, suspensions, player data

| Provider | Notes |
|---|---|
| **Sportmonks** | Injuries/suspensions feed + an "Expected Lineups" model (algorithmic, based on squad data + injury/suspension history) — paid add-on (€159–199/mo) |
| **API-Football** | Includes lineups (confirmed, once announced) and basic injury endpoints in its standard plans |
| **Wyscout (Hudl)** | Strongest player-level scouting data + video, industry standard for clubs, but priced/licensed for scouting departments, not a natural fit for an odds/edge product |

**Assessment:** lineups/injuries are a **Phase 2+ nice-to-have**, not a
day-one requirement — and they are exactly the kind of data where the
leakage rules in Section 4 of the brief matter most (an announced lineup 60
minutes before kickoff must never leak into a prediction generated 48 hours
earlier). We start with confirmed-lineup timestamps from whichever base
provider we pick (API-Football or Sportmonks both carry it) and defer the
paid "expected lineups" model add-on until there's a proven use for it.

## 5. Odds — pre-match, historical, and market movement

| Provider | What it offers | Price | Notes |
|---|---|---|---|
| **The Odds API** | Live odds from ~40 mainstream bookmakers; historical odds snapshots at 10-min intervals from Jun 2020, 5-min intervals from Sep 2022 | Free tier (limited), paid tiers scale with request volume; **historical calls cost 10× a normal credit** | Straightforward REST, well documented, good for both live scanning and CLV backtesting — but historical access is the expensive part, which matters a lot for Section 9 (CLV) and Section 13 (backtesting) |
| **Betfair Exchange API + Historical Data** | Real exchange prices (not bookmaker-quoted odds) — the closest thing to a "true market" price, incl. Betfair Starting Price (BSP) | Free tier: last-traded-price only, 1-min granularity, no volume. Paid tiers: full order-book depth, volume, since 2016. Commercial redistribution requires a Vendor/Software Vendor license | Exchange data is arguably the best reference price for CLV, since it reflects two-sided liquidity, not a single bookmaker's risk position |
| **Sportmonks odds feed** | Bundled into the same platform as match data (via TXOODS), broad bookmaker coverage | Included/add-on depending on plan | Convenience win: one vendor, one schema, for match + odds data |
| **Football-Data.co.uk** | Closing + (for some bookmakers) opening odds bundled into the historical CSVs | Free | Only covers a fixed set of bookmakers per season and stops at closing price — fine for backtest seeding, not for live scanning |
| **OddsPortal / other odds-comparison sites** | Broad odds-comparison coverage via scraping | Free (scraping) | ToS explicitly restricts commercial reuse — **excluded from production use**, may only inform manual research |

**Assessment:** for the **Market Edge Engine** (Section 8) and **CLV
analysis** (Section 9), we need both (a) a live multi-bookmaker feed and (b)
a defensible "true price" reference. Plan: **The Odds API** for live
multi-bookmaker scanning (feeds the edge detector across many books at
once), **Betfair Exchange** as the closing-line / CLV reference price
(exchange price is a stronger baseline than any single bookmaker's line),
and **Football-Data.co.uk** odds columns to seed historical backtests before
we pay for The Odds API's 10×-cost historical endpoint. This is also the
first place the product could hit a licensing wall if bookmaker coverage
needed later isn't in The Odds API's ~40-book panel — flagged as a Phase 9
risk, not resolved here.

## 6. Recommendation summary (Phase 0 conclusion)

| Data domain | Primary source (commercial path) | Secondary / cross-check | Research-only (never production) |
|---|---|---|---|
| Results, fixtures, team stats | Sportmonks | API-Football | — |
| xG / advanced stats | Sportmonks xG add-on | — | Understat, FBref (offline feature research) |
| Lineups / injuries | Sportmonks or API-Football (base plan) | — | Sportmonks "Expected Lineups" (deferred) |
| Odds — live, multi-book | The Odds API | Sportmonks odds feed | OddsPortal-style comparison sites |
| Odds — true/closing reference | Betfair Exchange (historical + streaming) | Football-Data.co.uk closing odds | — |
| Historical backtesting seed corpus (results + odds, 2000–present) | Football-Data.co.uk (free CSVs) | — | — |

**Why this combination and not "the best single API":** no single vendor in
this market bundles (a) broad multi-league coverage, (b) licensed xG, (c)
multi-bookmaker live odds, and (d) a true-price exchange reference. Anyone
claiming one API does all of that at a bootstrap price is a resale/aggregator
whose own upstream licensing needs the same diligence — hence a small
best-of-breed stack per domain, unified behind our own ingestion layer
(Section 3 of `DATA.md`) so a provider swap later only touches one adapter,
not the model or product layer.

**Explicit non-decision:** this document does **not** commit spend to any
paid plan. Phase 2 (data ingestion) starts against the **free** sources
(football-data.org free tier + Football-Data.co.uk historical CSVs +
Understat for offline xG research) to build and validate the ingestion
pipeline, leakage tests, and baseline models end-to-end before paying for
Sportmonks/The Odds API/Betfair. This matches the brief's Section 27 rule:
prove predictive capability before scaling spend.

## Sources

- [Sportmonks Football API](https://www.sportmonks.com/football-api/)
- [Sportmonks Pricing](https://www.sportmonks.com/football-api/plans-pricing/)
- [Sportmonks Expected Lineups](https://www.sportmonks.com/football-api/expected-lineups-api/)
- [football-data.org](https://www.football-data.org/)
- [football-data.org Pricing](https://www.football-data.org/pricing)
- [Football-Data.co.uk](https://football-data.co.uk/)
- [Football-Data.co.uk Notes](https://www.football-data.co.uk/notes.txt)
- [The Odds API — Docs v4](https://the-odds-api.com/liveapi/guides/v4/)
- [The Odds API — Historical Odds](https://the-odds-api.com/historical-odds-data/)
- [Betfair Developer Program — API Overview](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/API+Overview)
- [Betfair Historical Data](https://historicdata.betfair.com/)
- [Betfair Exchange Historical Data Services API](https://developer.betfair.com/historical-data-services-api/)
- [StatsBomb Open Data (GitHub)](https://github.com/statsbomb/open-data)
- [Opta vs. StatsBomb vs. Wyscout comparison](https://gamecode.ai/insights/articles/opta-vs-statsbomb-vs-wyscout/)
- [understatAPI (PyPI)](https://pypi.org/project/understatapi/)
- [Sports Betting Law overview — IMGL](https://www.imgl.org/sports-betting-law/)

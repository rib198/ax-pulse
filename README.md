# AX Pulse — AI Trend Intelligence Dashboard

> The 5-minute brief that turns public AI signals into commercial alpha.
> Bilingual (EN / ع), Linear-grade dark UI, ranked opportunities you can act on.

---

## Run it (zero install)

```bash
./start.command
```

This launches a local Python web server on `http://127.0.0.1:8000` and opens the landing page in your browser.

To use a different port:

```bash
PORT=9000 ./start.command
```

Stop with `Ctrl+C`.

## Radar v0

Collect AI signals from free official/public sources:

```bash
./pulse-radar
```

Outputs:

- `data/radar/raw_items.json`
- `data/radar/signals.json`
- `data/radar/opportunities.json`

Optional Feedly support:

```bash
export FEEDLY_TOKEN="..."
export FEEDLY_STREAM_ID="..."
./pulse-radar
```

Optional X API support:

```bash
./setup-x-token.command
./x-radar.command --x-limit 25
```

The token is saved in macOS Keychain, or read from `X_BEARER_TOKEN` if you prefer environment variables. It is not written to any project file.
The default X query is intentionally narrow and multilingual: it looks for AI posts with pain, cost, launch, need, or opportunity language in English, Arabic, Japanese, Chinese, and Korean, and skips reposts.

---

## What's inside

| Page | Purpose |
|------|---------|
| `index.html` | Landing — hero, pricing tiers, waitlist capture |
| `dashboard.html` | **Today's Brief** — headline, stats, top opportunities, trending clusters |
| `trending.html` | Filterable grid of all trending clusters with sparklines |
| `opportunities.html` | Full ranked list with novelty / momentum / revenue / ease scoring |
| `categories.html` | Category breakdown with growth deltas |

### Top-right toggle
`EN` / `ع` flips the entire UI to Arabic with proper RTL layout, IBM Plex Sans Arabic typography, and translated brief content.

---

## File map

```
ax-pulse/
├── index.html              landing + pricing
├── dashboard.html          today's brief
├── trending.html           cluster grid
├── opportunities.html      ranked opportunities
├── categories.html         category breakdown
├── start.command           local launcher (Python)
├── assets/
│   ├── css/
│   │   ├── tokens.css      design tokens (Linear-inspired)
│   │   └── app.css         component styles
│   └── js/
│       ├── app.js          i18n, data loading, page rendering
│       └── sidebar.js      shared sidebar injector
└── data/
    ├── i18n.json           EN + AR translations
    ├── brief.en.json       today's brief in English
    ├── brief.ar.json       today's brief in Arabic
    ├── opportunities.json  6 ranked opportunities
    ├── clusters.json       12 trending clusters
    └── categories.json     10 AI categories with deltas
```

---

## Design system

Borrowed from **Linear** (via [nexu-io/open-design](https://github.com/nexu-io/open-design)):

- **Surfaces**: `#08090a` deep, `#0f1011` panel, `#191a1b` elevated
- **Text**: `#f7f8f8` primary (never pure white), `#8a8f98` muted
- **Borders**: `rgba(255,255,255,0.08)` semi-transparent, never solid dark
- **Typography**: Inter Variable with `cv01, ss03` features, signature **weight 510**
- **Letter-spacing**: aggressive negative at display sizes (`-1.4px` at 64px)
- **Mono**: JetBrains Mono for numbers, labels, and signal-coded UI
- **Arabic**: IBM Plex Sans Arabic with relaxed line-height (1.9) and natural weights

**AX Pulse signature**: electric green `#7CFF6B` reserved for CTAs, accents, and "signal detected" moments — replacing Linear's indigo with a unique brand identity.

---

## What the demo proves

1. **Bloomberg-meets-Linear visual polish** — premium, dense, calm.
2. **Daily Brief** is a tangible artifact a buyer can grasp in 5 seconds.
3. **Opportunity scoring** (novelty / momentum / revenue / ease) is the differentiated artifact — no other AI newsletter ranks ideas this way.
4. **Bilingual EN/AR with RTL** — competitive moat for the MENA market.
5. **Pricing surface ready** — Free / Pro $29 / Team $99 / Enterprise (Saudi vertical).

---

## Migration to production (next 12 hours)

Once you're ready to leave the static demo:

| Layer | Move to |
|-------|---------|
| Hosting | Vercel (drop-in for the static files; or migrate to Next.js) |
| Database | Supabase (Postgres + pgvector for embeddings) |
| Ingestion | Official RSS + Hacker News + Reddit + GitHub + optional Feedly stream → cron every 4h |
| Classification | Claude Haiku 4.5 (batched, JSON output) |
| Briefs + opportunities | Claude Sonnet 4.6 (with prompt caching) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Email | Resend |

The JSON data shape in `data/` is exactly the contract the Next.js API routes will return — so the frontend stays unchanged.

---

## License

Demo build. Personal use. Production deployment requires respecting each source's API, RSS, and platform terms.

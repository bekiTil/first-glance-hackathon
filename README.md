# Ticket Watch

**An agent-run company for the Zero Human Company Hackathon NYC (Oct 24, 2026).**

A customer says what tickets they want ("Knicks under $80, any Friday in November, 2 seats"). An agent turns
that into a checklist they confirm, they pay **$3 on Whop**, and an agent checks prices **every 15 minutes**
and alerts them by **email and text** when a verified match appears. If no match appears before the event,
the agent **refunds automatically**. Seven agents run the business (product, sales, support, money,
marketing, compliance, research), and two **Terac** studies with real people teach the agent what a good
deal is and prove it improved.

**Deadline: submissions lock at 6:45pm. Agents take over at about 4:00pm.**

---

## Team and roles

| Person | Role | Owns (files) |
|---|---|---|
| **Bereket** | Engine & Infrastructure (repo owner) | Railway deploy · DB + shared contracts (`enums.py`, `schemas.py`, `models.py`, `agents/base.py`) · worker/scheduler (`worker.py`) · **Watcher agent** (`agents/watcher.py`, `agents/intake.py`, `agents/deal_score.py`) · SeatGeek/Ticketmaster (`integrations/tickets.py`) · **Solari** (`integrations/solari.py`) · **Compliance** guardrails (`agents/guardrails.py`) · `integrations/llm.py` · `api/watches.py`, `api/links.py`, `api/company.py`, `stats.py` |
| **Natnael** | Payments, Messaging & Customers | **Everything payment-related**: the Whop business is in Natnael's name; he holds the Whop keys, payouts, refunds and ad spend (`integrations/whop.py`, `api/webhooks.py`, `payments` table) · **Finance agent** (`agents/finance.py`) · **Support agent** (`agents/support.py`) · email + text (`integrations/notify.py`) · phone codes + magic-link login (`api/phone.py`, `api/me.py`) |
| **Yared** | Growth, Research & Product Face | React site (`frontend/`, incl. the shared `src/api/client.ts`) · **CEO agent** (`agents/ceo.py`) · **Growth agent** (`agents/growth.py`, `integrations/exa.py`, `api/events.py`) · **Research agent** + Terac studies (`agents/research.py`, `integrations/terac.py`, `studies` table) · demo + submission |

> **Money rule:** only Natnael creates or logs into the Whop account, holds `WHOP_*` keys, or receives revenue.
> Other agents call functions in `integrations/whop.py`; they never hold Whop credentials.

### What's already done (shared) vs. what's yours

**Done and shared.** Use these as they are, and change them only through their owner:
- **Config + environment:** `.env.example`, `backend/app/config.py`, `pyproject.toml` + `uv.lock`,
  `frontend/package.json` + `package-lock.json`, `Dockerfile`
- **Contracts:** `enums.py`, `schemas.py`, `models.py`, `db.py`, `jobs.py`, `deal_score.DEFAULT_WEIGHTS`,
  the `guardrails.check_outbound` signature, `openapi.json` → `frontend/src/api/types.ts`, `frontend/src/api/client.ts`
- **Plumbing:** the agent interface (`agents/base.py`), the agent registry (`agents/__init__.py`), the worker +
  scheduler (`worker.py`), the Claude helper (`integrations/llm.py`), app wiring (`main.py`), and the dev
  fake checkout (`api/dev.py`)
- **Mock mode** for every integration, so anyone can run without keys
- **Every API route exists** with its final request/response types. The bodies return
  `501 Not implemented yet: TODO(owner)` until the owner builds them.

**Yours to build.** Every stub says exactly what it must do in its docstring:

| Bereket | Natnael | Yared |
|---|---|---|
| `agents/watcher.py`, `agents/intake.py`, `agents/deal_score.py` (`matches`, `score`), `agents/guardrails.py` (rules), `api/watches.py`, `api/links.py`, `api/company.py`, `stats.py`, real `integrations/tickets.py` + `integrations/solari.py`, Railway | `agents/finance.py`, `agents/support.py`, `api/webhooks.py`, `api/phone.py`, `api/me.py`, real `integrations/whop.py` + `integrations/notify.py`, the Whop account | `agents/ceo.py`, `agents/growth.py`, `agents/research.py`, `api/events.py`, real `integrations/exa.py` + `integrations/terac.py`, every page in `frontend/src/pages/`, Terac studies, demo |

**Finish line:** `backend/tests/test_end_to_end.py` is the whole flow and is skipped for now. When your
parts are in, remove its skip line together and make it pass.

Find your work with: `grep -rn "TODO(Bereket)\|TODO(Natnael)\|TODO(Yared)" backend frontend/src`

---

## Setup (Windows, macOS, Linux)

You need **[uv](https://docs.astral.sh/uv/getting-started/installation/)** (it installs the right Python, 3.12,
for you) and **Node 22** (`.nvmrc`).

```bash
git clone https://github.com/bekiTil/ticket-watch.git && cd ticket-watch
cp .env.example .env            # Windows: copy .env.example .env

# backend
cd backend
uv sync                          # creates .venv with exact versions from uv.lock
uv run pytest -q                 # contract tests must pass; end-to-end is skipped until parts land
uv run uvicorn app.main:app --reload --port 8000     # terminal 1: API
uv run python -m app.worker                          # terminal 2: agents (or --once)

# frontend
cd ../frontend
npm ci                           # exact versions from package-lock.json
npm run dev                      # terminal 3: http://localhost:5173 (proxies /api to :8000)
```

**Check your setup:** http://localhost:8000/docs lists every route with its exact request/response shape.
Unbuilt routes answer `501 … TODO(owner)`, and unbuilt agents are skipped quietly by the worker.
`curl -X POST localhost:8000/api/dev/run-worker` runs every agent once instead of waiting 15 minutes.
Once the parts are built, the full no-keys flow is: open http://localhost:5173 → start a watch → confirm
(the fake Whop checkout marks it paid) → run-worker → alerts print in the API terminal →
http://localhost:5173/company shows the Company Log.

**Mock mode:** every service has a `MOCK_*` flag in `.env` (all `true` by default). Turn yours off only after
adding your keys to **your own** `.env`. In mock mode, the phone verification code is always `123456`.

---

## How it fits together

```
Customer ─► React site ─► POST /api/watches ─► intake agent builds checklist
                │                      └─► confirm ─► Whop checkout (Natnael) ─► webhook
                ▼                                                               │
         /company page ◄── decision_log ◄── agents ◄── jobs table ◄─────────────┘
                                             ▲
              worker: Watcher 15m · Growth 30m · CEO / Finance / Research 60m · jobs every 5s
```

**Rules everyone follows:**
1. **API routes only enqueue jobs** (`app/jobs.py`). The `agents` worker runs the agents.
2. **Every agent decision is logged:** `ctx.log(action, reason, **data)`. That log *is* the Company Log page the judges see.
3. **Everything outbound goes through guardrails first:** `if ctx.check(OutboundKind.sms, text, ...)`. This covers emails, texts, posts, ads, price changes and refunds.
4. **All datetimes are naive UTC** (`app.db_time.utcnow()`).
5. **Claude calls go through `app.integrations.llm`**: `ask_text`, `ask_json` (schema-guaranteed JSON), or `run_tools` (agent loop). Always pass `mock=` so the flow runs offline. The model defaults to `claude-opus-5-5`, and refusal fallbacks are on.

### Shared contracts (change only through the owner, and say so in team chat)

| Contract | File | Owner |
|---|---|---|
| Status/type values | `backend/app/enums.py` | Bereket |
| API + domain shapes (`Checklist`, `Listing`, `WatchOut`, …) | `backend/app/schemas.py` | Bereket |
| Database tables | `backend/app/models.py` | Bereket |
| Agent interface (`Agent`, `AgentContext`) | `backend/app/agents/base.py` | Bereket |
| Integration function signatures | `backend/app/integrations/*.py` | each file's owner |
| API contract for the frontend | `openapi.json` → `frontend/src/api/types.ts` | Bereket regenerates, Yared consumes |
| Frontend API calls | `frontend/src/api/client.ts` | Yared |

After changing `schemas.py` or any route: `cd backend && uv run python scripts/export_openapi.py && cd ../frontend && npm run gen:api`,
then commit `openapi.json` and `types.ts` together.

Schema changes: tables are created automatically on start. After a column change, delete `backend/dev.db` locally. On Railway, ask Bereket.

### API

| Method | Path | What |
|---|---|---|
| POST | `/api/watches` | request text + email (+ phone) → checklist, follow-up questions, matching events |
| GET / PATCH | `/api/watches/{id}` | read / edit the checklist (before payment) |
| POST | `/api/watches/{id}/confirm` | → Whop `checkout_url` |
| POST | `/api/phone/send-code`, `/api/phone/verify` | 6-digit text code |
| POST | `/api/webhooks/whop` | Whop payment → Finance agent |
| POST | `/api/webhooks/sms` | Twilio incoming text → Support agent (1 bought · 2 keep · 3 not what I wanted · STOP) |
| GET | `/api/reply/{token}/{bought\|keep\|reject}` | email buttons → Support agent |
| GET | `/go/{token}` | tracked buy link → logs click → ticket site |
| POST / GET | `/api/me/login`, `/api/me/watches?token=` | magic-link "my watches" |
| GET | `/api/company/log`, `/api/company/stats` | Company Log page |
| GET | `/api/free-events` | free NYC events (Exa) |
| GET | `/api/proof/{token}` | Solari screenshot proving a deal existed |
| GET / POST | `/api/dev/fake-pay/{id}`, `/api/dev/run-worker` | mock mode only |

Interactive docs: http://localhost:8000/docs

---

## Git workflow (three PCs, one repo)

- Branch per task: `bereket/watcher-seatgeek`, `natnael/whop-checkout`, `yared/company-log-page`.
- Edit only the files you own (table above). Need a shared contract changed? Ask its owner.
- `git pull --rebase origin main` before you push. Merge to `main` **at least every ~45 minutes**, small and often.
- Run `uv run pytest -q` (backend) or `npm run build` (frontend) before merging.
- **Never commit `.env` or keys.** Share keys privately. Railway variables are set by each service's owner.
- Formatting: `uv run ruff format . && uv run ruff check .` in `backend/`.

## Deploy (Railway, owner: Bereket)

One Railway project built from this repo's `Dockerfile`, with three parts:
1. **web** service: variable `SERVICE=web`. It gets the public domain, and `PUBLIC_API_URL` / `PUBLIC_WEB_URL` = that domain.
2. **agents** service: same repo and image, variable `SERVICE=agents`.
3. **Postgres**: set `DATABASE_URL` on both services to Railway's Postgres URL.

Copy the other `.env` values into both services, with **real keys and `MOCK_*=false`** for live services.
Natnael sets the `WHOP_*` variables himself. Whop's webhook URL is `https://<web domain>/api/webhooks/whop`, and
Twilio's incoming-message webhook is `https://<web domain>/api/webhooks/sms`.

## Timeline

| Time | Bereket | Natnael | Yared |
|---|---|---|---|
| now–2:30 | Railway + deploy this skeleton; SeatGeek/TM/Solari keys | Whop business + $3 product + API key + webhook; Resend; Twilio trial | Terac MCP + **launch Study 1 now**; Exa key |
| 2:30–3:30 | Real SeatGeek search + prices; deal score | Real checkout / webhook / refund; email | Site polish; Growth + CEO agents |
| 3:30 | **Deploy real version** | | |
| 3:30–4:00 | Solari verification + screenshots | Texts + replies; Finance checks | Research agent; Study 1 → deal weights |
| **4:00** | **Hands off: agents run the company** | | Marketing push |
| 4:00–5:30 | Fixes | Fixes | **Study 2 by ~4:30**; Company Log page |
| 5:30–6:45 | Freeze at 6:00 | Freeze at 6:00 | Before/after, demo video, **submit before 6:45** |

## Hackathon requirements checklist

- [ ] Agents run the company (Company Log shows decisions from every agent after 4:00)
- [ ] **Terac MCP** used: real human input with a measured before/after (Study 1 → weights → Study 2)
- [ ] Built on **Whop**; **all payments through Whop** (no Stripe)
- [ ] **Real, organic revenue** (Whop dashboard + `/api/company/stats`)
- [ ] Exa (free events + research) and Solari (listing verification) for the sponsor tracks

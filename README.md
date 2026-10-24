# FirstGlance

**Do people get your startup in 10 seconds?** An agent-run company for the Zero Human Company Hackathon NYC (Oct 24, 2026).

A founder pastes their landing page URL plus one sentence about what they do, then pays **$15 on Whop**.
An agent reads their hero (headline, subhead, button) and Claude writes a clearer version. **About 10 real
people from Terac** each see *one* version for 10 seconds, then answer "What does this company do?" and "How
likely are you to sign up? (1-5)". Claude grades the answers, and the founder gets a report: *"3/5 understood
yours, 5/5 understood ours. Here's the new copy."* If our version doesn't win, they're **refunded
automatically**. We also run FirstGlance on our own landing page; that's our Terac before/after.

**Deadline: submissions lock at 6:45pm. Agents take over by ~4:30pm.**

---

## Team and roles

| Person | Role | Builds (files) |
|---|---|---|
| **Bereket** | Engine & Infrastructure (repo owner) | **Tester agent** (`agents/tester.py`): launches one Terac study per test, grades the answers, delivers the report · page reading + rewrite (`agents/intake.py`) · Solari screenshots (`integrations/solari.py`) · order/report routes (`api/tests.py`) · Company Log + stats (`api/company.py`, `stats.py`) · guardrail rules (`agents/guardrails.py`) · Railway deploy |
| **Natnael** | Payments, Messaging & Customers | **Everything payment-related**: the Whop business is in Natnael's name, and he holds the keys, payouts and refunds (`integrations/whop.py`, `api/webhooks.py`) · **Finance agent** (`agents/finance.py`): payment → start test; money-back guarantee · **Support agent** (`agents/support.py`, `api/support.py`) · email (`integrations/notify.py`) |
| **Yared** | Growth, Research & Product Face | **Test page** participants see (`frontend/src/pages/TestTaker.tsx`, `api/testpage.py`) ✅ · **Research agent** (`agents/research.py`): tests our own landing page = the before/after ✅ · CEO + Growth agents ✅ · Terac/Exa/Bluesky clients ✅ · pages `NewTest`, `Report`, `Landing`, `CompanyLog` ✅ · Terac/Exa keys · demo + submission |

> **Money rule:** only Natnael creates or logs into the Whop account, holds `WHOP_*` keys, or receives revenue.
> Other agents call functions in `integrations/whop.py`; they never hold Whop credentials.

✅ = already built. Everything else is a stub whose docstring says exactly what to build. Find your work with:
`grep -rn "TODO(Bereket)\|TODO(Natnael)\|TODO(Yared)" backend frontend/src`

### Order of work (it's a relay; the arrows are hand-offs)

1. **Bereket:** `intake.read_hero` + `write_rewrite` → `POST /api/tests` + `GET /api/tests/{id}` → **deploy to Railway ASAP**
   (Terac participants need the public https site).
2. **Natnael:** Whop product ($15) + checkout + webhook → Finance `payment_received` (marks paid, queues `run_test`).
3. **Yared:** ✅ `/t/:id` test page + `/api/t` routes + Research self-test (queues a `run_test` job; it launches once the Tester and the public site exist).
4. **Bereket:** Tester: launch study → grade → deliver report.
5. **Natnael:** report email, refund guarantee, Support agent.
6. **Everyone:** turn on `tests/test_end_to_end.py` (remove its skip line) and make it pass together.

---

## Setup (Windows, macOS, Linux)

You need **[uv](https://docs.astral.sh/uv/getting-started/installation/)** (it installs Python 3.12 for you) and **Node 22** (`.nvmrc`).

```bash
git clone https://github.com/bekiTil/first-glance-hackathon.git && cd first-glance-hackathon
cp .env.example .env            # Windows: copy .env.example .env

cd backend
uv sync                          # exact versions from uv.lock
uv run pytest -q                 # contract tests must pass; end-to-end is skipped until parts land
uv run uvicorn app.main:app --reload --port 8000     # terminal 1: API (+ docs at /docs)
uv run python -m app.worker                          # terminal 2: agents (or --once)

cd ../frontend
npm ci
npm run dev                      # terminal 3: http://localhost:5173 (proxies /api to :8000)
```

**Mock mode:** every service has a `MOCK_*` flag in `.env` (all `true` by default), so you can work with no keys.
Turn yours off only after adding your keys to **your own** `.env`. Dev helpers (mock mode only):
- `GET /api/dev/fake-pay/{id}`: pretend Whop checkout
- `POST /api/dev/fake-answers/{id}?n=10`: pretend Terac people answered
- `POST /api/dev/run-worker`: run every agent once

Unbuilt routes answer `501 Not implemented yet: TODO(owner)`. Unbuilt agents are skipped quietly by the worker.

---

## How it fits together

```
Founder ─► /test/new ─► POST /api/tests (read hero + rewrite) ─► confirm ─► Whop checkout (Natnael)
                                                                              │ webhook
Terac people ─► /t/:id (10 s, 2 questions) ─► test_answers        Finance ◄────┘ paid → run_test job
                                   ▲                                │
                                   └──── Tester: launch Terac study ◄┘ → grade → report email → /report/:id
                                                                          └─► Finance refunds if ours lost
Company Log ◄── decision_log ◄── every agent     (CEO 60m · Growth 30m · Research 60m · Tester 2m · Finance 10m)
```

**Rules everyone follows:**
1. **API routes only enqueue jobs** (`app/jobs.py`). The `agents` worker runs the agents.
2. **Every agent decision is logged:** `ctx.log(action, reason, **data)`. That log *is* the public Company Log. Never put emails in `data`.
3. **Everything outbound goes through guardrails first:** `if ctx.check(OutboundKind.email, html): ...`. This covers emails, posts, ads, price changes and refunds.
4. **All datetimes are naive UTC** (`app.db_time.utcnow()`).
5. **Claude calls go through `app.integrations.llm`**: `ask_text`, `ask_json` (schema-guaranteed JSON), `run_tools`. Always pass `mock=`. The model defaults to `claude-opus-5-5`.

### Shared contracts (change only through the owner, and say so in team chat)

| Contract | File | Owner |
|---|---|---|
| Status/type values (`TestStatus`, `Arm`, `JobType`, …) | `backend/app/enums.py` | Bereket |
| Shapes (`HeroCopy`, `TestOut`, `TestPageOut`, `TestResults`, `PaymentEvent`, `Stats`, …) | `backend/app/schemas.py` | Bereket |
| Tables (`page_tests`, `test_answers`, `payments`, `company_state`, `decision_log`, `jobs`) | `backend/app/models.py` | Bereket |
| Agent interface (`Agent`, `AgentContext`) + registry | `backend/app/agents/base.py`, `agents/__init__.py` | Bereket |
| Integration function signatures | `backend/app/integrations/*.py` | each file's owner |
| API contract | `openapi.json` → `frontend/src/api/types.ts` | whoever changes a route regenerates both |
| Frontend API calls | `frontend/src/api/client.ts` | Yared |

After changing `schemas.py` or a route: `cd backend && uv run python scripts/export_openapi.py && cd ../frontend && npm run gen:api`,
then commit `openapi.json` and `types.ts` together. After a column change, delete `backend/dev.db` locally.

### API

| Method | Path | Owner | What |
|---|---|---|---|
| POST | `/api/tests` | Bereket | URL + what you do + email → original hero + our rewrite (draft) |
| GET | `/api/tests/{id}` | Bereket | test status, answers so far, results (report page polls it) |
| POST | `/api/tests/{id}/confirm` | Bereket | → Whop `checkout_url` |
| POST | `/api/webhooks/whop` | Natnael | Whop payment → Finance agent |
| POST | `/api/support` | Natnael | contact form → Support agent |
| GET | `/api/t/{id}?participant=` | Yared | what one Terac participant sees (one arm) |
| POST | `/api/t/{id}/answers` | Yared | their answer |
| GET | `/api/landing-copy` | Yared | our current (winning) landing copy |
| GET | `/api/self-test` | Yared | our own before/after |
| GET | `/api/company/log`, `/api/company/stats` | Bereket | Company Log page |

---

## Git workflow

- Work on `main` (or short `yourname/task` branches off it). Edit only the files you own; ask the owner for contract changes.
- `git pull --rebase` before you push, and push **at least every ~45 minutes**, small and often.
- Run `uv run pytest -q` (backend) or `npm run build` (frontend) before pushing.
- **Never commit `.env` or keys.** Share keys privately.

## Deploy (Railway, owner: Bereket)

One Railway project from this repo's `Dockerfile`:
1. **web** service (`SERVICE=web`) with the public domain. Set `PUBLIC_WEB_URL` and `PUBLIC_API_URL` to that **https** domain.
2. **agents** service (`SERVICE=agents`).
3. **Postgres**, with `DATABASE_URL` on both services.

Copy the `.env` values to both services, with real keys and `MOCK_*=false` for live services. Natnael sets the `WHOP_*`
variables himself, and the Whop webhook URL is `https://<web domain>/api/webhooks/whop`.

## Timeline

| Time | Bereket | Natnael | Yared |
|---|---|---|---|
| now–3:45 | read hero + rewrite, tests routes, **deploy** | Whop product + checkout + webhook | test page + `/api/t`, Terac API key |
| 3:45–4:30 | Tester: launch + grade + deliver | Finance (paid → run_test), report email | Research self-test launches; NewTest + Report pages |
| **4:30** | **Hands off: agents run the company**. Sell to the ~200 teams in the room | | |
| 4:30–6:00 | fixes, stats | refunds, Support | Growth posts, Company Log, demo script |
| 6:00–6:45 | freeze | freeze | demo video, **submit before 6:45** |

## Hackathon requirements checklist

- [ ] Agents run the company (Company Log shows every agent deciding after 4:30)
- [ ] **Terac** with a measured before/after: our self-test (`/api/self-test`), plus every customer report
- [ ] Built on **Whop**; **all payments through Whop** (no Stripe)
- [ ] **Real, organic revenue**
- [ ] Exa (Growth research) and Solari (page screenshots) for the sponsor tracks
- [ ] Be upfront in the demo: PickFu/Lyssna sell 10-second tests. Ours is the full loop (test → AI rewrite → proof → refund) run by agents.

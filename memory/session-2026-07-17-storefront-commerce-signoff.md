# Session resume — 2026-07-17 (storefront commerce + Docker Funnel sign-off)

**Branch:** `master` @ `0d6fe8e` (synced with `origin/master`)  
**Working tree:** clean at sign-off  
**Runtime at sign-off:** Docker stack was healthy on Tailscale Funnel; local API/storefront killed earlier. Operator may shut Docker with `docker compose down`.

---

## What shipped this session

### A — Web ↔ Telegram order-flow parity (tests)
- `tests/unit/services/test_order_flow_parity.py` — shared spine TG id vs web OAuth id  
- `tests/unit/services/test_commerce_http_parity.py` — HTTP commerce_api vs TG services  
- Same path: delivery → cart → cash/PromptPay → orders → kitchen status shape  

### B — Storefront commerce UI (C-08 → C-17)
- `apps/storefront/src/lib/commerce.ts`  
- Pages: `/{brand}/cart`, `/checkout`, `/orders`, `/orders/{code}`  
- Item page: **Add to cart** (not Contact) when caps allow  
- Nav/footer: Cart + Orders  
- Playwright: `apps/storefront/e2e/commerce.spec.ts` (3 tests green vs live API)  
- Seed: `SEED_SNUS_COMMERCE_MODE=full_store|hybrid|portfolio` (`run_public_api` defaults full_store)  

### C — CARD-39 OAuth go-live wiring
- Preflight `_check_web_oauth`  
- Browser OAuth errors → `/{brand}/login?error=…`  
- Redirect URI prefers `PUBLIC_SITE_URL/.../google/callback`  
- `.env.example` + compose OAuth env passthrough  
- **CARD-42** runbook: where to get Google Client ID/secret  

### D — Other WIP committed/pushed
- LINE channel depth + QR host  
- Physical invite cards (CARD-41) + migrations  
- Funnel deploy: Caddy + Tailscale serve configs  
- CARD-34 flow specs package under `docs/Specifications/flows/`  

### Commits (this arc)
```
0d6fe8e feat: LINE channel depth, invite cards, Funnel deploy, flow specs
40584f2 docs: CARD-42 Google OAuth credentials runbook + board log
bd4286c feat(auth): CARD-39 Google OAuth go-live ops wiring
ae05314 feat(storefront): web cart/checkout/orders parity with Telegram spine
```

---

## Live URLs (when Docker + Funnel up)

| What | URL |
|------|-----|
| Funnel site | https://telegram-shop-1.tail31319c.ts.net/ |
| Demo brand | https://telegram-shop-1.tail31319c.ts.net/snus-demo |
| Login | …/snus-demo/login |
| Health | …/health |
| Catalog API | …/api/public/brands |

Verified: storefront **200**, API **200**, Funnel proxy → edge `:8080`.

---

## Docker only (preferred runtime)

```powershell
# Up
docker compose up -d --build

# Status / logs
docker compose ps
docker compose logs -f bot
docker compose logs -f storefront

# Down (full stop)
docker compose down
# volumes preserved unless: docker compose down -v
```

**Do not** run local `python scripts/run_public_api.py` + `npm run dev` alongside Docker unless ports are free and intentional.

---

## Ops residual (next human)

1. **Google OAuth live** — [CARD-42](../docs/done/CARD-42-google-oauth-credentials-runbook.md)  
   - Set `OAUTH_GOOGLE_CLIENT_ID` / `SECRET`, `WEB_SESSION_SECRET`, `OAUTH_DEV_LOGIN=false`, `WEB_COOKIE_SECURE=true`  
   - Restart bot; check `GET /api/public/auth/config` → `google_enabled: true`  
2. Preflight still warns if secrets missing / BTC pool low (non-blocking).  
3. Optional board next: CARD-33 IG · CARD-36 polish · LINE credential go-live  

---

## Open board (do not re-open spine)

| Card | Status |
|------|--------|
| CARD-39 | ~95% — paste Google secrets only |
| CARD-42 | ✅ runbook done |
| CARD-36 | ~90% optional polish |
| CARD-33 | ~55% |
| CARD-37 | parked |
| Spine 29–32 · 35 · 38 · 40 · 16 code · 34 | done / archived |

**Law:** adapters → services → domain. No handler→domain shortcuts for shared caps. No web lead forms “for parity” on Telegram.

---

## Resume checklist (next session)

1. Read `docs/CLEAR-START.md`  
2. `git pull` · `git status` (expect clean on master)  
3. `docker compose ps` — if down: `docker compose up -d`  
4. Smoke Funnel `/snus-demo` + `/health`  
5. Pick next: Google secrets · IG · LINE ops  

---

## Sign-off

**Date:** 2026-07-17  
**Session:** Storefront commerce parity + Playwright + CARD-39/42 docs + Docker Funnel deploy  
**Local stack:** stopped earlier (no host :9090/:4321 app)  
**Docker:** was healthy; shut down on explicit sign-off request if operator ran `docker compose down`  
**Push:** yes — `origin/master` at `0d6fe8e`  

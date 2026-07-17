# Session resume — 2026-07-18 (multi-vertical demos + contrast + stock photos)

## Sign-off status

**Runtime:** Docker stack + Tailscale Funnel healthy.  
**Git:** `master` @ `8b110dc` (pushed). Clean working tree.

### What shipped this session

| Area | Status |
|------|--------|
| Multi-vertical demo seeds | ✅ snus · food · coffee · herb · bakery · grocery |
| 3 branches / brand | ✅ real Bangkok-style addresses, phones, geo |
| Clipart placeholders | ✅ `tests/test-data/ph-*.png` (Pillow) |
| Unsplash stock photos | ✅ coffee + food `stock-*.jpg` (free license) |
| Theme contrast law | ✅ seed (`theme_contrast.py`) + storefront (`theme.ts` + token CSS) |
| Admin store + lead harness | ✅ `store_admin` · list/update leads · unit tests |
| Funnel demos live | ✅ all 6 brands on public URL |

### Commits (this arc)

- `158b2ff` — multi-vertical templates, branches, harnesses  
- `7cecd1d` — contrast-safe text (no white-on-white sand hardcodes)  
- `8b110dc` — Unsplash stock photos for coffee/food  

### Regenerate all demos

```powershell
docker compose up -d --build
docker compose exec bot python scripts/seed_site_templates.py --template all --force --snus-mode full_store
# Stock photos (if missing):
python scripts/fetch_demo_stock_images.py
```

### Demo URLs (Funnel)

Base: `https://telegram-shop-1.tail31319c.ts.net`

| Path | Notes |
|------|--------|
| `/snus-demo` | Editorial NOVA-style, 18+ gate, vector cans |
| `/coffee-demo` | Light warm palette, stock photos, modifiers |
| `/food-demo` | Dark food palette, stock photos, spice mods |
| `/herb-demo` | 21+ gate, hybrid inquire/order |
| `/bakery-demo` | Light peach, daily limits |
| `/grocery-demo` | Dark navy, low Silom stock tests |

API: `/api/public/brands` · media: `/media/local/stock-coffee-latte.jpg`

### Key paths

| Path | Role |
|------|------|
| `scripts/seed_site_templates.py` | Single entry: snus + verticals + stock fetch |
| `scripts/fetch_demo_stock_images.py` | Unsplash → `tests/test-data/stock-*.jpg` |
| `bot/services/seed_demo_verticals.py` | Food/coffee/herb/bakery/grocery packs |
| `bot/services/seed_snus_demo.py` | NOVA snus + multi-branch |
| `bot/services/theme_contrast.py` | Seed-time contrast enforcement |
| `bot/services/store_admin.py` | Admin store list/edit/toggle |
| `apps/storefront/src/lib/theme.ts` | Runtime contrast + CSS vars |
| `apps/storefront/src/styles/global.css` | `.t-fg` / `.t-muted` / panel tokens |

### Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/services/test_theme_contrast.py tests/unit/services/test_demo_verticals.py tests/unit/services/test_admin_ops_harness.py tests/unit/services/test_site_template_harness.py -q --no-cov
```

### Not in this session

- Google OAuth secrets paste (CARD-42 ops)  
- Herb/bakery/grocery Unsplash photos (still clipart placeholders)  
- Telegram admin FSM UI for lead list (service layer only)  

### Next session suggestions

1. Paste Google OAuth secrets and verify `/login` on Funnel  
2. Optional: stock photos for bakery/grocery/herb  
3. CARD-33 / LINE go-live ops  

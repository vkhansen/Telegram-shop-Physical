## Summary

<!-- What changed and why (1–3 sentences). -->

## CARD-40 / multi-channel gate

> Shared features go through **application services** + **capability masks**.  
> Web-only funnel and TG-ops are **intentional non-parity**, not debt.  
> Scorecard: `docs/done/CARD-40-parity-scorecard.md`

- [ ] **Service boundary:** Business rules live in `bot/services/*` or `bot/platform/*` (not only in a Telegram handler / Astro page).
- [ ] **Capability key:** Uses an existing `CAPABILITY_KEYS` entry (or adds one + updates the [parity matrix](../docs/done/CARD-40-parity-matrix.md)).
- [ ] **Adapters noted:** Web / Telegram / both — mask defaults documented if changed.
- [ ] **Non-parity honest:** Web-only (`leads`, `booking`, marketing, `age_gate`, OAuth) or TG-ops (`admin_console`, kitchen, driver, broadcast) marked N/A — **not** cloned onto the other surface “for parity.”
- [ ] **Deep links only for funnel on TG:** If TG needs lead/book conversion, use `bot/platform/deep_links.py` URL buttons — no new lead/book FSM.
- [ ] **Tests:** Service and/or mask/enforcement tests updated.

### Reject list (do not merge if any apply without design card)

- [ ] New inventory / payment / ticket / lead **business** logic only in `bot/handlers/**`
- [ ] Second messaging channel (IG/LINE/…) before CARD-40 freeze (complete)
- [ ] Cloning web lead/booking forms into Telegram for “parity”

## Test plan

```bash
# Targeted (adjust paths)
python -m pytest tests/unit/platform/ tests/unit/services/ tests/unit/ai/ -q --no-cov
```

- [ ] Local/CI tests green for touched areas

## Risk / rollout

<!-- Migrations, env vars, feature flags, rollback notes — or "n/a". -->

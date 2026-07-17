# Tailscale Serve + Funnel

Expose the **pretty storefront + public API** over HTTPS without a VPS.

Funnel → `127.0.0.1:8080` (Caddy edge) → Astro storefront + bot API.

| Mode | File | Reachable by |
|------|------|--------------|
| **Funnel** (default) | `serve-funnel.json` | Anyone on the public internet |
| **Private** | `serve-private.json` | Tailnet members only (MagicDNS / Tailscale IP) |

Public URL shape after join:

```text
https://telegram-shop.<your-tailnet>.ts.net/              ← pretty Astro site
https://telegram-shop.<your-tailnet>.ts.net/snus-demo     ← brand home
https://telegram-shop.<your-tailnet>.ts.net/health        ← API health
https://telegram-shop.<your-tailnet>.ts.net/api/public/...
```

Postgres (`5432`), Redis (`6379`), and pgweb (`8081`) stay **tailnet-only** via the socat proxy. They are never Funnelled.

## Prerequisites (Tailscale admin)

1. **MagicDNS** on — [DNS settings](https://login.tailscale.com/admin/dns)
2. **HTTPS certificates** on — same page
3. **Funnel allowed** in [Access controls](https://login.tailscale.com/admin/acls), for example:

```json
{
  "nodeAttrs": [
    {
      "target": ["*"],
      "attr": ["funnel"]
    }
  ]
}
```

Narrow `target` to `tag:container` or the `telegram-shop` node if you prefer least privilege.

4. Auth key in `.env` as `TS_AUTHKEY=...`  
   ([keys](https://login.tailscale.com/admin/settings/keys) — reusable recommended)

## Compose env

```env
TS_AUTHKEY=tskey-auth-...
# serve-funnel.json (public) or serve-private.json (tailnet HTTPS only)
TS_SERVE_CONFIG_FILE=serve-funnel.json
MONITORING_API_KEY=long-random-secret
```

After the node is online, set public base URLs to the Funnel host:

```env
PUBLIC_MEDIA_BASE_URL=https://telegram-shop.<your-tailnet>.ts.net
```

## Commands

```bash
docker compose up -d --build
docker compose logs -f tailscale
docker exec telegram_shop_tailscale tailscale status
docker exec telegram_shop_tailscale tailscale serve status
docker exec telegram_shop_tailscale tailscale funnel status
# If Funnel is tailnet-only after a reset, re-enable public:
docker exec telegram_shop_tailscale tailscale funnel --bg http://127.0.0.1:8080
```

Pretty site (verified): `https://telegram-shop-1.<tailnet>.ts.net/` · brand e.g. `/snus-demo`

Switch to tailnet-only HTTPS:

```env
TS_SERVE_CONFIG_FILE=serve-private.json
```

Then `docker compose up -d tailscale` (or full stack recreate).

## Security notes

- Funnel publishes the **entire** `:9090` app (including `/dashboard` and metrics). Set a strong `MONITORING_API_KEY` so those routes stay protected.
- `/api/public/*`, `/media/*`, `/health`, and webhook paths are intentionally unauthenticated — that is by design for storefront/channel adapters.
- Do not Funnel database or Redis ports.
- Revoke leaked auth keys in the Tailscale admin console.

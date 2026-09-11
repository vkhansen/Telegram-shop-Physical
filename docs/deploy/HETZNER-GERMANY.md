# Hetzner Falkenstein (Germany) — cheapest secure deploy

**Location:** `fsn1` (Falkenstein, Saxony). Same Cloud list price as Nuremberg (`nbg1`); Falkenstein is the default because stock is usually better. One box only.

**Goal:** lowest monthly bill that can actually run this stack, unique SSH keys, Tailscale-only admin, code push via git + compose.

This repo already ships Tailscale Funnel in `docker-compose.yml`. The VPS is a cheap host; **public HTTP/HTTPS stays off the Hetzner NIC**. Telegram, storefront, and API go out through Tailscale Funnel (`https://telegram-shop.<tailnet>.ts.net`).

## 1. Cheapest machine that will not OOM

This compose stack is Postgres + Redis + bot + Astro storefront + Caddy + Tailscale. **2 GB RAM is too small.**

| Plan | Specs | Germany (`fsn1` / `nbg1`) | Verdict |
|------|--------|---------------------------|---------|
| CPX11 / CAX11 / CX23-class 2 GB | 2 GB | Cheapest on paper | **Do not use** — OOM under compose |
| **CX22** | 2 vCPU, **4 GB**, 40 GB | **~€3.79–€4.51/mo** + IPv4 | **Use this** — cheapest viable single server |
| CPX22 | 2 vCPU, 4 GB, 80 GB | slightly more | If CX22 is sold out |
| CAX21 (ARM) | 4 vCPU, 8 GB | ~€6.30/mo | More RAM; extra if images are amd64-only pain |

**Skip Primary IPv4** (`€0.50/mo`) if you can bootstrap over **IPv6 + Hetzner web console**, then join Tailscale and never need a public v4. Telegram bots and Funnel do not need a public IPv4 on the VPS.

**Do not enable** Hetzner backups (~20%) until you have a snapshot you care about. One manual snapshot after first successful `compose up` is enough.

**OS:** Ubuntu 24.04.

Approximate monthly floor: **CX22, IPv6-only, no backups ≈ €3.79–€4.51**. With IPv4: **+€0.50**.

If `fsn1` is out of CX22, retry `nbg1` (`-Location nbg1`) — same price, still Germany.

## 2. Unique SSH key (do not reuse GitHub / laptop default)

One **ed25519 key pair per server**, stored outside the git repo.

On Windows (operator machine):

```powershell
.\scripts\hetzner\New-HetznerSshKey.ps1
```

That writes:

- `%USERPROFILE%\.ssh\hetzner-fsn-telegram-shop_ed25519` (private, `600`)
- `..._ed25519.pub` (this goes to Hetzner)
- never commit either file

Hetzner Console → **Security → SSH keys → Add** → paste the `.pub` → name `telegram-shop-fsn-YYYYMMDD`.

Rotate by generating a **new** key, attaching it, then deleting the old one from the server and from Hetzner. Do not copy this private key to a second laptop; generate another named key (`telegram-shop-fsn-laptop2`) if a second operator needs access.

## 3. Network / firewall (before first boot)

Hetzner Cloud Firewall, attached at create time:

| Direction | Protocol | Port | Source | Action |
|-----------|----------|------|--------|--------|
| In | TCP | 22 | your current public IPv4 **or** none | Allow only during bootstrap |
| In | UDP | 41641 | `0.0.0.0/0` + `::/0` | Tailscale (optional; DERP works without it) |
| In | ICMP | — | any | Allow (path MTU) |
| In | everything else | — | — | **Deny** |
| Out | any | — | — | Allow (Telegram API, Docker Hub, Tailscale coordination) |

**Do not open 80/443.** Funnel does not use them on the host.

After Tailscale SSH works, **remove port 22 from the firewall** (or set source to empty). Public SSH is then closed. Rescue still works via Hetzner Console.

## 4. Provision (one command)

Prerequisites on the operator PC:

1. [hcloud CLI](https://github.com/hetznercloud/cli/releases) **or** set `HCLOUD_TOKEN` and use the script’s REST path.
2. API token: Hetzner Console → Security → API tokens → **Read & Write**, project-scoped.
3. Unique SSH public key from §2.

```powershell
$env:HCLOUD_TOKEN = "..."   # do not put in git
.\scripts\hetzner\New-HetznerDeServer.ps1 `
  -SshPublicKeyPath "$env:USERPROFILE\.ssh\hetzner-fsn-telegram-shop_ed25519.pub"
```

Defaults: location `fsn1`, type `cx22`, name `telegram-shop-fsn`, Ubuntu 24.04, cloud-init from `scripts/hetzner/cloud-init.yaml`.

Cloud-init does:

- deploy user `deploy` (sudo, SSH key only)
- disable password SSH and root password login
- install Docker Engine + compose plugin
- install Tailscale (does **not** join until you pass an auth key)
- unattended-upgrades
- fail2ban on sshd (harmless once 22 is firewalled)

## 5. Tailscale join (host + compose)

Two layers:

| Layer | Role |
|-------|------|
| **Host Tailscale** | SSH to the box (`tailscale ssh deploy@telegram-shop-fsn`) without public port 22 |
| **Compose `tailscale` service** | Funnel + MagicDNS for the app (already in `docker-compose.yml`) |

Create **two** auth keys in [Tailscale keys](https://login.tailscale.com/admin/settings/keys):

1. **Host:** reusable=false, ephemeral=false, tagged `tag:hetzner-host`, expiry 90d.
2. **Container:** reusable=true (compose restarts), tagged `tag:container`, as in `deploy/tailscale/README.md`.

On the server (first time, from Hetzner Console or IPv6 SSH):

```bash
sudo tailscale up --ssh --hostname=telegram-shop-fsn --auth-key=tskey-auth-HOST...
```

`--ssh` enables Tailscale SSH. ACL example:

```json
{
  "tagOwners": {
    "tag:hetzner-host": ["autogroup:admin"],
    "tag:container": ["autogroup:admin"]
  },
  "ssh": [
    {
      "action": "accept",
      "src": ["autogroup:admin"],
      "dst": ["tag:hetzner-host"],
      "users": ["deploy", "root"]
    }
  ],
  "acls": [
    { "action": "accept", "src": ["autogroup:admin"], "dst": ["*:*"] }
  ],
  "nodeAttrs": [
    { "target": ["tag:container"], "attr": ["funnel"] }
  ]
}
```

Then close public :22 in the Hetzner firewall.

Put the **container** key in server `.env` as `TS_AUTHKEY` (never commit).

## 6. Push code and start the stack

On the operator PC, after host Tailscale is up:

```powershell
# SSH config snippet (~/.ssh/config)
# Host telegram-shop-fsn
#   HostName telegram-shop-fsn   # MagicDNS
#   User deploy
#   IdentityFile ~/.ssh/hetzner-fsn-telegram-shop_ed25519
#   IdentitiesOnly yes

git remote add fsn deploy@telegram-shop-fsn:/opt/telegram-shop.git   # optional bare repo
```

Simplest path (no extra remotes):

```bash
# on server
sudo mkdir -p /opt/telegram-shop
sudo chown deploy:deploy /opt/telegram-shop

# on laptop
rsync -az --delete --exclude .git --exclude .env --exclude node_modules \
  ./ deploy@telegram-shop-fsn:/opt/telegram-shop/
scp .env.production deploy@telegram-shop-fsn:/opt/telegram-shop/.env
```

Or clone from GitHub **on the server** using a **deploy key** (another unique ed25519, read-only, GitHub repo → Settings → Deploy keys). Do not put your personal GitHub SSH key on the VPS.

```bash
cd /opt/telegram-shop
# copy .env (secrets only on server)
docker compose build bot storefront
docker compose up -d
docker compose logs -f tailscale bot
```

App access:

- Public storefront/API: Funnel URL in `deploy/tailscale/README.md`
- SSH / pgweb / Postgres / Redis: **tailnet only**

## 7. Secrets and uniqueness checklist

| Secret | Unique per env | Where |
|--------|----------------|-------|
| SSH host keypair | yes | operator `~/.ssh/hetzner-fsn-*` |
| GitHub deploy key | yes, read-only | GitHub + `/home/deploy/.ssh/` |
| `HCLOUD_TOKEN` | project-scoped | operator env, not the VPS |
| Tailscale host auth key | one-shot | used once, then delete |
| `TS_AUTHKEY` (compose) | tagged `tag:container` | server `.env` |
| `POSTGRES_PASSWORD`, `TOKEN`, `MONITORING_API_KEY`, `WEB_SESSION_SECRET` | production values, not `.env.example` | server `.env` |

`.env` is gitignored. Never rsync it into a public repo.

## 8. Day-2

- `docker compose pull && docker compose up -d --build` after git pull / rsync.
- `sudo unattended-upgrades` is already enabled; reboot when kernel updates (`sudo reboot`; Tailscale comes back with persisted state).
- Snapshot in Hetzner Console after a known-good deploy.
- If the box is lost: recreate with the same script, new SSH key name, restore `.env` from your password manager, clone, compose up.

## 9. What this does *not* do

- It does not open the bot or Postgres on the public internet.
- It does not use Hetzner Load Balancer or extra volumes (cost). 40 GB CX22 disk is enough for this image set.
- It does not run Kubernetes.
- It does not use Node on the operator machine; rsync/git and Docker on Ubuntu only.
- It is not Ashburn/Hillsboro. US locations are out of scope for this plan.

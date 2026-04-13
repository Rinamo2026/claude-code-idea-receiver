# Networking & Mobile Access

idea-receiver runs on your local machine (port 8702).  
On the same Wi-Fi, your phone can reach it at `http://<your-pc-ip>:8702` — no extra setup needed.

To access from **anywhere** (commute, coffee shop, different network), you need to expose port 8702 to the internet. Options below, easiest first.

---

## Option 1: Tailscale Funnel (recommended)

[Tailscale](https://tailscale.com/) creates a private mesh network between your devices, and Funnel exposes one port publicly over HTTPS.

```bash
# Install Tailscale, then:
tailscale funnel 8702
```

Update `.env`:
```env
RP_ID=yourhost.your-tailnet.ts.net
ORIGIN=https://yourhost.your-tailnet.ts.net
```

**Pros**: One command, automatic HTTPS, no port forwarding, free tier available.

---

## Option 2: ngrok

```bash
ngrok http 8702
```

ngrok prints a public URL like `https://abc123.ngrok-free.app`.

Update `.env`:
```env
RP_ID=abc123.ngrok-free.app
ORIGIN=https://abc123.ngrok-free.app
```

**Note**: The URL changes every restart on the free tier. Use a paid plan or `ngrok config` for a stable domain.

---

## Option 3: Cloudflare Tunnel

```bash
cloudflared tunnel --url http://localhost:8702
```

Or set up a named tunnel for a stable subdomain on your own domain.  
See [Cloudflare Tunnel docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/).

---

## Option 4: WireGuard (self-hosted VPN)

If you already run a WireGuard server (e.g. on a VPS), route traffic to your local machine:

1. Peer your PC into the WireGuard network
2. Point your phone at `http://<wireguard-peer-ip>:8702`
3. Update `.env` with the WireGuard peer IP or hostname

No HTTPS is provided by WireGuard itself — add a reverse proxy (nginx, Caddy) if you need it.

---

## WebAuthn & RP_ID

WebAuthn ties passkey credentials to a specific `RP_ID` (the domain/hostname).  
If you change the access URL, you must update `RP_ID` and `ORIGIN` in `.env` — and re-register your passkey.

| Access method | RP_ID | ORIGIN |
|--------------|-------|--------|
| Local only | `localhost` | `http://localhost:8702` |
| Tailscale Funnel | `yourhost.ts.net` | `https://yourhost.ts.net` |
| ngrok | `abc123.ngrok-free.app` | `https://abc123.ngrok-free.app` |
| Custom domain | `ideas.yourdomain.com` | `https://ideas.yourdomain.com` |

---

## Security Notes

- idea-receiver trusts local loopback connections without authentication (no forwarded headers = direct local access)
- When exposed via a tunnel or proxy, full WebAuthn authentication is required
- The classification pipeline calls `claude -p` as a subprocess — your ideas text is sent to the Claude API

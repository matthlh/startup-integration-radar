# Deploying Integration Scout

A simple two-service deployment:

```
┌──────────────────────────┐         ┌──────────────────────────────────┐
│  Vercel — Next.js front  │  HTTPS  │  Railway / Render — FastAPI back │
│  https://<app>.vercel    │ ──────▶ │  https://<api>.up.railway.app    │
│  Reads NEXT_PUBLIC_API_  │         │  Persistent volume at $DATA_DIR  │
│  BASE                    │         │  Serves /api/*                   │
└──────────────────────────┘         └──────────────────────────────────┘
```

Frontend on **Vercel** because Next.js is the path of least resistance there. Backend on **Railway** first because Railway gives you a persistent volume in one click — the app keeps the seed CSV and the analyzed-companies JSON store on disk, and you don't need Postgres yet. **Render** works equally well and uses the same start command; the choice is mostly account-level preference.

Postgres / Supabase is a future upgrade once the local JSON store becomes a bottleneck (well past 1k companies).

---

## Required environment variables

### Backend (Railway / Render)

| Variable | Required | Value | Notes |
|---|---|---|---|
| `DATA_DIR` | yes (hosted) | `/data` or `/var/data` | Must point at the mounted volume so seed/analyzed data persists across deploys. |
| `ALLOWED_ORIGINS` | yes | `https://<your-app>.vercel.app` | Comma-separate multiple origins. Local dev defaults work without this. |
| `ENABLE_EXTERNAL_API_CALLS` | no | `false` | Keep false unless you want Exa/Anthropic calls. |
| `EXA_API_KEY` | no | `<key>` | Only needed when running `discover --live`. |
| `ANTHROPIC_API_KEY` | no | `<key>` | Only needed for the optional LLM demo path. |
| `USER_AGENT` | recommended | `IntegrationScoutBot/0.3 contact=you@example.com` | Identifies our crawler to remote sites. |
| `PORT` | auto | (set by host) | Railway/Render inject this. The start command already reads it. |

### Frontend (Vercel)

| Variable | Required | Value |
|---|---|---|
| `NEXT_PUBLIC_API_BASE` | yes | `https://<your-backend>/api` |

---

## Deploy the backend on Railway

1. Push the repo to GitHub if you haven't.
2. <https://railway.app> → **New Project** → **Deploy from GitHub repo** → pick this repo.
3. In **Settings**, set **Root Directory** to `backend`. Railway will detect `nixpacks.toml` and `railway.json` and use them.
4. **Add a Volume**: Project → **Volumes** → **New Volume**, mount at `/data`. Note: free-tier plans don't include volumes; use the $5/mo plan.
5. In **Variables**, set:
   - `DATA_DIR=/data`
   - `ALLOWED_ORIGINS=https://<vercel-app>.vercel.app` (you can update this after Vercel is up)
   - `USER_AGENT=IntegrationScoutBot/0.3 contact=you@example.com`
6. Trigger a deploy. The build uses `pip install -r requirements.txt`; the start command is `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
7. Visit `https://<railway-url>/api/health`. You should see:
   ```json
   {"ok": true, "service": "integration-scout", "storage": "/data", "version": "0.3.0", "external_calls_enabled": false}
   ```

### Pushing data to Railway

The hosted backend starts with an empty seed CSV. Three ways to populate it:

- **Easy**: open the Vercel dashboard once it's live → use the "Add to seed list" form. Each row is `POST`ed to the backend and persists on the volume.
- **Bulk**: scp a local `seed_companies.csv` or `companies.json` to the volume via Railway's shell.
- **Re-analyze**: the CLI talks to the local filesystem, not the hosted backend, so running `python scripts/radar.py run` locally and then uploading `companies.json` is the easiest way to seed a real list before going live.

---

## Deploy the backend on Render (alternative)

1. <https://render.com> → **New** → **Blueprint** → point at the repo. Render will read `render.yaml` and provision the service + a 1 GB persistent disk at `/var/data`.
2. After the disk is created, set `DATA_DIR=/var/data` in the service env (already in the blueprint).
3. Set `ALLOWED_ORIGINS` to your Vercel URL.
4. Healthcheck path is `/api/health` (already in the blueprint).
5. Trigger the first deploy.

Alternatively (without Blueprints), create a Web Service manually:
- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Attach a 1 GB disk at `/var/data`
- Same env vars as above

---

## Deploy the frontend on Vercel

1. <https://vercel.com> → **Add New** → **Project** → import the repo.
2. **Root Directory**: `frontend`.
3. **Framework Preset**: Next.js (auto-detected).
4. **Environment Variable**: `NEXT_PUBLIC_API_BASE=https://<railway-or-render-url>/api`.
5. Deploy. Vercel hands you a `*.vercel.app` URL.
6. Go back to the backend host and update `ALLOWED_ORIGINS` to include that URL. Redeploy the backend so CORS picks up the change.

---

## Persistent storage warning

Hosts like Railway and Render run containers with **ephemeral filesystems by default**. Without a mounted volume, every redeploy wipes `seed_companies.csv` and `companies.json`. If you skip the volume step, the app still runs but loses state on every push — you'll lose review-status edits.

If you ever switch hosts: zip the `$DATA_DIR` contents (`seed_companies.csv`, `companies.json`) and copy them to the new volume. The format is plain JSON/CSV, no migration needed.

---

## Testing after deployment

```bash
# Healthcheck
curl https://<backend-url>/api/health

# Companies endpoint (empty list on first deploy)
curl https://<backend-url>/api/companies

# Add a seed via API
curl -X POST https://<backend-url>/api/seeds \
  -H "content-type: application/json" \
  -d '{"domain":"monk.ai","company_name":"Monk"}'

# CSV export
curl "https://<backend-url>/api/exports/clay.csv"
```

Then load `https://<vercel-app>.vercel.app` and confirm:
- The empty state shows.
- "Add to seed list" works.
- "Analyze now" runs against the hosted backend (this can take ~10s while it crawls).
- "Export approved" downloads the right CSV.

---

## Rollback and debug

- **Backend won't start**: check Railway/Render logs for stack traces. The most common cause is a missing env var or `DATA_DIR` pointing at an unwritable path.
- **Frontend can't reach backend**: check the browser console for CORS errors. The backend's `ALLOWED_ORIGINS` env var must include the exact Vercel origin (`https://app.vercel.app`, not `app.vercel.app`).
- **Empty data after redeploy**: the volume isn't mounted. Verify `DATA_DIR` is `/data` (Railway) or `/var/data` (Render) and matches the volume mount path.
- **Rollback Railway**: Deployments tab → click an older deploy → **Redeploy**.
- **Rollback Render**: Service → **Manual deploy** → pick a previous commit.
- **Rollback Vercel**: Deployments tab → click an older deploy → **Promote to Production**.

---

## What's intentionally NOT included

- **No auth.** The hosted backend is wide open. Treat the Vercel URL as a soft secret and don't link to it publicly. Adding Vercel Access on top of the dashboard is the cheapest first step when you need a gate.
- **No Postgres.** The JSON store handles hundreds of companies fine. Move to Supabase when the file gets unwieldy.
- **No email sending.** Outreach copy is generated and exported to Clay; Clay handles sending if you wire that up there.
- **No paid API auto-call.** Exa and Anthropic stay off unless you flip `ENABLE_EXTERNAL_API_CALLS=true` and supply keys.

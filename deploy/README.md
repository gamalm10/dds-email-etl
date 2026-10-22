# DDS production deployment (A-part_ai_server)

Published to Portainer (endpoint 3, single-node Swarm `ubuntu-ai` @ 192.168.5.40)
as stack **`dds`** and served at **https://dds.a-part.com**.

## Components

| Service | Image | Notes |
|---|---|---|
| `dds-db` | `registry2.onehealthnetwork.net/dds-db:v1` | `mariadb:11` + `migrations/` baked into `/docker-entrypoint-initdb.d`; data on volume `dds_db_data` |
| `dds-api` | `registry2.onehealthnetwork.net/dds-api:v1` | FastAPI + Node sidecar; backend network only |
| `dds-frontend` | `registry2.onehealthnetwork.net/dds-frontend:v1` | Next.js standalone; proxies `/api/*` to `http://dds-api:8000`; on `proxy` + `backend` |

Networks `proxy` and `backend` are external Swarm overlays shared with the other stacks.

## Prerequisites

- DNS: `dds.a-part.com` → `192.168.5.40` (internal) **and** the public IP (for Let's Encrypt HTTP-01). Done.
- Caddy (plain `caddy:alpine`, static Caddyfile at `/home/config/caddyfile` — the `caddy.*` labels are inert) must contain:
  ```
  dds.a-part.com {
      reverse_proxy dds-frontend:3000
  }
  ```
  No `encode` directive, so chat SSE is not buffered.

## Build & push (build on the server — the Mac has no route to Docker Hub)

The Mac can only reach the internal registry, so images are built on the server
and pushed to it in one step, using a throwaway `docker:cli` builder container
with the host Docker socket mounted:

1. Tar the build context locally, mirroring `.dockerignore`:
   `tar -czf ctx.tar.gz --exclude='.git' --exclude='.venv' --exclude='emails'
   --exclude='docs' --exclude='tests' --exclude='__pycache__' --exclude='.env'
   --exclude='deploy/dds_dump.sql' --exclude='dds-frontend/node_modules' .`
2. Via the Portainer Docker API (endpoint 3): `POST /containers/create`
   (`docker:cli`, `Cmd` = extract context + `docker build` + `docker push`,
   `Binds: ["/var/run/docker.sock:/var/run/docker.sock"]`).
3. Upload files into it with `PUT /containers/{id}/archive?path=/` — the body is
   a tar whose single entry is the payload file (`ctx.tar`, `config.json` with
   the registry auth block).
4. `POST /containers/{id}/start`, poll `GET /containers/{id}/json` until it
   exits, read build output via `GET /containers/{id}/logs`, then delete the
   builder.

Do not use `POST /endpoints/{id}/docker/build` directly: it fails with
`Unable to proxy the request via the Docker socket ... broken pipe` on this
setup, and hijacked exec streams return no output, so the archive-upload +
logs-read pattern above is the reliable path.

Build contexts:

- API: repo root, `dockerfile=Dockerfile`
- Frontend: `dds-frontend/`, `dockerfile=Dockerfile`
- DB: repo root, `dockerfile=deploy/dds-db.Dockerfile`

The registry caps the **compressed blob** size (a 200 MB incompressible layer is
rejected, 300 MB of zeros is fine). The API image is therefore split so no single
layer is too large (apt bootstrap and nodejs in separate layers; the sidecar agent
is installed once, globally, not twice).

Releases bump the image tag in the stack file. Bumping the shared `DDS_TAG`
stack env var redeploys all three services, so for a single-service change pin
that service's `image:` line to the new tag instead (as done for
`dds-api:v4`), then force the swarm service update
(`POST /services/{id}/update` with the bumped image) if Portainer's stack
update does not roll it.

## Stack

`deploy/docker-compose.portainer.yml`. Env vars are supplied from `.env`
(MariaDB, IMAP, SMTP, `JWT_SECRET`/`JWT_REFRESH_SECRET`, `OPENAI_API_KEY`).
The frontend needs the DB + JWT vars because it has its own auth routes.

## Data migration

```bash
docker exec dds-email-etl-dds-db-1 mariadb-dump -uroot -p"$MARIA_ROOT_PASSWORD" \
  --single-transaction --hex-blob --routines --triggers dds > deploy/dds_dump.sql
```

Import into the running `dds-db` task (archive upload + exec) once the DB is up.
Verified row-for-row against the local database.

## Known issues

- `migrations/006_brand_attribution.sql` alters `dds_priority_actions`, which is
  only created later in `009_reconcile_schema.sql`. A **fresh** init (no data
  import) therefore fails at 006. This deploy is unaffected because the dump
  recreates the full schema, but the ordering should be fixed before any
  clean-slate deployment.
- `JWT_SECRET` / `JWT_REFRESH_SECRET` were rotated to strong random values
  (86-char `token_urlsafe(64)`); the live values are held in the Portainer
  stack `dds` env and in the gitignored `.env`. Rotating them invalidates all
  existing sessions. The API and frontend must share the same `JWT_SECRET`.
- `deploy/dds_dump.sql` (production data + password hashes) was accidentally
  committed and pushed; it has been purged from git history (force-pushed) and
  is now gitignored. The old commit object may still be retrievable on GitHub
  by SHA until their garbage collection runs.
- DB credentials (`dds` and root) were rotated to strong random values on both
  the production and local databases; live values are in the Portainer stack
  `dds` env and the gitignored `.env`. `MARIADB_*` stack env only applies on
  first init — existing users must be changed with `ALTER USER`.
- `deploy/dds_dump.sql` remains on the local disk (gitignored) as a migration
  artifact; delete it once no longer needed.

# Project Documentation

A Flask app + MySQL database, containerized with Docker Compose, hardened, secured with Docker secrets, and wired into a CI pipeline with Trivy image scanning.

## 1. Containerization

Split the app into three services defined in `docker-compose.yml`:

- **web** — Flask app built from `app/app.dockerfile`
- **db** — MySQL 8 built from `mysql/mysql.dockerfile`, with schema and stored procedures loaded from `mysql/init/init.sql` on first boot
- **adminer** — web UI for browsing the database

The Flask app talks to MySQL over TCP using the compose service name `db` as host. Credentials, DB name, and host are injected via environment variables so the same image runs in any environment.

## 2. Hardening

Each service is locked down:

- **web** runs as a non-root user (uid 1001) created in the Dockerfile
- **cap_drop: [ALL]** on `web` and `adminer` — no Linux capabilities
- **no-new-privileges:true** — setuid binaries can't elevate
- **read_only: true** with a tmpfs `/tmp` on `web` — nothing persists to disk
- Resource limits per service (CPU + memory) so a runaway process can't take down the host

The `db` service is intentionally not hardened the same way — MySQL needs `CHOWN`, `SETUID`, and `SETGID` to initialize and drop privileges internally.

## 3. Secrets

Passwords moved out of `docker-compose.yml` into files under `secrets/`:

- `mysql_root_password.txt`, `mysql_password.txt`, `mysql_user.txt`, `mysql_database.txt`
- Mounted at `/run/secrets/` in each container
- `secrets/` is gitignored — never committed
- MySQL reads them via the official `*_FILE` env vars; Flask reads them via a `read_secret()` helper with fallback to plain env vars

Result: credentials no longer appear in the compose file, in container env, or in `docker inspect` output.

## 4. Trivy Scanning

Trivy scans the built images for known CVEs:

- **web** — mostly Debian base package findings with no fix available upstream, plus a few `libmariadb3` findings tied to `mysqlclient`
- **db** — Oracle Linux base findings and Go stdlib CVEs inside the `gosu` binary

Findings are triaged, not blindly fixed. Non-reachable CVEs (like `gosu`, which only runs `setgid`/`setuid`/`exec` once at startup) are documented and suppressed via `.trivyignore` with rationale in `SECURITY.md`.

## 5. CI Pipeline

`.github/workflows/build-push.yml` triggers on any `v*.*.*` tag (and manual dispatch). It:

1. Builds both images in parallel using a matrix
2. Pushes them to GitHub Container Registry (GHCR)
3. Scans each with Trivy, uploading SARIF to the Security tab
4. Fails the build on **CRITICAL with a fix available**, respecting `.trivyignore`

Images are referenced by digest during scanning so the workflow works identically for tag pushes and manual runs. The image prefix is lowercased because Docker references must be all-lowercase.

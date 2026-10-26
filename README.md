# Olist E-commerce Data Platform

A beginner-friendly data engineering portfolio project. OLIST-002 provides a
Python development environment and local PostgreSQL; ingestion and analytics
will be implemented in later tickets.

Target architecture: Olist CSV → MinIO (Bronze) → PostgreSQL (Raw) → dbt
(Staging, Intermediate, Marts) → Power BI. Airflow comes after reliable manual runs.

Business requirements and architecture are documented in
[requirements](docs/requirements.md), [architecture](docs/architecture.md), and
[design decisions](docs/decisions.md). Their open business questions remain open.

## Prerequisites

- Windows 11 and PowerShell, running from this repository's root directory.
- Python 3.11, Git, and Docker Desktop running Linux containers with Compose.
- An available localhost port (5432 by default).

```powershell
python --version
docker version
docker compose version
```

Confirm Python reports **3.11.x**. If `python` points elsewhere, use `py -3.11`
or the absolute path to your Python 3.11 executable for environment creation.
Docker must show a reachable server as well as a client.

## Install the Python environment

If `.venv` already exists, inspect `.venv/pyvenv.cfg` first. An environment made
in WSL/Linux or with another Python version cannot be reused on Windows.
Preserve it before creating the Windows environment:

```powershell
# Only when replacing an incompatible environment; choose an unused backup name.
Rename-Item -LiteralPath .venv -NewName .venv.previous
```

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Select `.venv\Scripts\python.exe` as the VS Code Python interpreter. Commands here
use it directly, so activation and execution-policy changes are unnecessary.
Optional activation: `.\.venv\Scripts\Activate.ps1`.

Runtime dependencies are pinned in `requirements.txt`: `psycopg[binary]` supplies
the PostgreSQL driver without a local compiler and `python-dotenv` loads local
configuration. Use Python 3.11; this simplified setup does not enforce the Python
version through package metadata. Transitive dependencies and the PostgreSQL
image digest are not locked.

Code runs directly from `src/`; the project is not installed as a package.
Package metadata, automated tests, and Ruff are deferred until needed. Installing requirements
does not generate a project `.egg-info` directory.

## Configure and start PostgreSQL

```powershell
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
```

Edit `.env` and replace the example password. Keep `.env` private; it is ignored
by Git. For passwords containing `$` or `#`, use single quotes around the value
to preserve the literal characters. Existing shell environment variables take
precedence over `.env` for both Python and Compose.

```powershell
docker compose up -d --wait
docker compose ps
```

Compose runs `postgres:16`, binds it to localhost, and stores database files in
the `postgres_data` named volume. `POSTGRES_PORT` controls the host port;
PostgreSQL uses port 5432 inside its container. The configured user is the image's
bootstrap superuser for local development. Layer schemas and separate application
roles are deferred.

## Verify

```powershell
.\.venv\Scripts\python.exe src/olist_platform/check_db.py
git check-ignore .env .venv/ data/
git status --short
```

The connectivity command executes `SELECT 1` with a five-second connection
timeout, prints success, and exits with code zero. Failure returns a nonzero
code without printing credentials; inspect `$LASTEXITCODE` immediately afterward.
Start PostgreSQL before running the connectivity check. Verification is manual
for now; no automated test framework is configured.

## Persistence and service lifecycle

```powershell
docker compose stop
docker compose start --wait
```

`docker compose down` removes the container/network but preserves the named
volume. A subsequent `docker compose up -d --wait` reuses the data. Do not add
`-v` to normal shutdown commands: that option deletes the database volume.

Optional manual persistence verification creates a disposable table in `public`:

```powershell
'CREATE TABLE public.olist002_persistence_probe (id integer); INSERT INTO public.olist002_persistence_probe VALUES (1);' | docker compose exec -T postgres sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker compose down
docker compose up -d --wait
'SELECT id FROM public.olist002_persistence_probe;' | docker compose exec -T postgres sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
'DROP TABLE public.olist002_persistence_probe;' | docker compose exec -T postgres sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

The query should return `1`. Use these commands in the local development
database only, and remove the probe after verification.

## Troubleshooting

- Docker connection failure: start Docker Desktop and wait for its Linux engine.
- Port conflict: change `POSTGRES_PORT` in `.env` and recreate the service with
  `docker compose up -d --wait`.
- Authentication failure after editing `.env`: initialization credentials apply
  only to a new volume. Changing `.env` does not update an existing database
  password. Restore matching credentials or intentionally change the database
  role password; preserve existing data.
- Python import failure: install `requirements.txt` using the same environment
  interpreter that runs the command. Run the connectivity script by its file
  path from the repository root.
- Inspect service errors with `docker compose logs --tail 50 postgres`. Avoid
  sharing expanded configuration or logs containing secrets.

## Repository layout

```text
docs/                         OLIST-001 requirements and design
src/olist_platform/            Python source and database check
compose.yaml                  PostgreSQL 16 and persistent volume
requirements.txt              Runtime dependencies
.env.example                  Tracked local configuration template
```

Local `.env`, virtual environments, `data/`, caches, and generated build files
are ignored. No datasets, ingestion, transformations, MinIO, dbt, Airflow, or
Power BI artifacts are included in this ticket.

# DevOps Practices — Django Ecommerce Web App

This document tracks the DevOps tooling and workflow currently implemented for this project.

## Stack Overview

| Area              | Tool / Practice                          |
|-------------------|-------------------------------------------|
| App framework     | Django 6.1 (Python 3.12)                  |
| Containerization  | Docker (single-stage `dockerfile`)        |
| Orchestration     | Docker Compose (single `web` service)     |
| CI/CD             | Jenkins (declarative pipeline)            |
| Trigger           | GitHub webhook → Jenkins                  |
| Registry          | Docker Hub                                |

## 1. Containerization (Docker)

The app is packaged using a single `dockerfile` at `ecom/dockerfile`:

- Base image: `python:3.12-slim`
- Installs dependencies from `requirements.txt`
- Copies application source into `/app`
- Exposes port `8000`
- Runs the Django dev server: `python3 manage.py runserver 0.0.0.0:8000`

> **Note:** this currently runs Django's built-in dev server inside the container. For anything beyond local/demo use, swap this for a production WSGI server (e.g. Gunicorn) behind a reverse proxy.

## 2. Local Orchestration (Docker Compose)

`ecom/docker-compose.yml` defines a single `web` service that:

- Runs the `myapp:latest` image
- Maps container port `8000` to host port `8000`
- Mounts `db.sqlite3` and `media/` as volumes, so data persists across container restarts

## 3. CI/CD Pipeline (Jenkins)

`ecom/Jenkinsfile` defines a declarative pipeline (`agent: docker-agent`) with three stages:

1. **Install Dependencies**
   - Creates a Python virtual environment (`venv`)
   - Installs packages from `requirements.txt`

2. **Test**
   - Activates the virtual environment
   - Runs `python3 manage.py test` (Django's built-in test runner)

3. **Build**
   - Builds the Docker image: `docker build -t myapp:latest .`
   - Tears down existing containers: `docker compose down`
   - Brings up the new containers: `docker compose up -d`
   - Verifies status: `docker compose ps`

### Trigger
The pipeline is wired to a **GitHub webhook**, so a push to the repository automatically kicks off install → test → build → redeploy on the Jenkins agent.

## 4. Test Coverage

A test suite exists across the core apps (`user_app`, `cart_app`, `payment_app`) covering:
- Registration, login, logout flows
- Cart creation, add/update/remove logic
- End-to-end checkout → payment → order confirmation
- Auth-required view redirects and per-user ownership isolation (403/404 on cross-user access)
- CSRF enforcement on POST forms

Lighter smoke coverage exists for `address_app`, `order_app`, and `product_app` (CRUD + URL resolution).

Run locally with:
```bash
python3 manage.py test
```

## 5. Known Gaps / Next Steps

These are recommended but **not yet implemented**:

- **Production hardening:** move `SECRET_KEY` to an environment variable, set `DEBUG=False`, configure `ALLOWED_HOSTS`, and enable Django's `SECURE_*` settings.
- **Production-grade app server:** replace `manage.py runserver` in the Dockerfile with Gunicorn/uWSGI + Nginx.
- **Database:** move off `db.sqlite3` (file-mounted volume) to a managed/production database (e.g. PostgreSQL) for anything beyond local demos.
- **Image tagging:** pipeline currently always builds/pushes `myapp:latest`; consider tagging by commit SHA or build number for rollback-ability.
- **Coverage reporting:** integrate `coverage.py` into the Jenkins `Test` stage to publish a coverage percentage.
- **Static/media storage:** move `media/` off local volume mounts to object storage (e.g. S3) for multi-instance deployments.
- **Secrets management:** no `.env` / secrets manager in use yet — required before this leaves a local Jenkins agent setup.

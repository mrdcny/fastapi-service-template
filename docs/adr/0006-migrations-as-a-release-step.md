# 6. Alembic migrations run as a release step, not at startup

- Status: accepted
- Date: 2026-10-26

## Context

Schema changes need to be versioned, reviewable and repeatable. They also need to run exactly once per release. Running migrations on app startup is common, but with several replicas starting at once they race each other, a slow migration makes pods fail their startup probes, and a failed migration crash-loops every pod.

## Decision

- Use **Alembic** for migrations, with hand-reviewed revision files under `migrations/versions/`.
- Run `alembic upgrade head` as a **Helm `pre-install,pre-upgrade` hook Job**. Helm waits for it to succeed before rolling out new pods. If it fails, the release fails and the old pods keep serving.
- The app never migrates itself.
- `migrations/env.py` reads the URL from the same `Settings` class as the app, so they can't point at different databases.
- CI runs upgrade, downgrade, upgrade, then `alembic check` to prove migrations round-trip and that the models match the schema.

## Consequences

- Migrations must be **backwards compatible with the previous release**, since old pods keep running against the new schema during a rollout. Destructive changes (dropping or renaming a column) are split across releases: expand, migrate code, then contract.
- Locally, run `make migrate` (or let `docker compose` run the `migrate` service).

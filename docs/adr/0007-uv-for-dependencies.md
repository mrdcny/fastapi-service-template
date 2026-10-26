# 7. uv for dependency management

- Status: accepted
- Date: 2026-10-26

## Context

We need a lockfile for reproducible builds, separate dev dependencies, and fast installs in CI and Docker. Options: pip with pip-tools, Poetry, uv.

## Decision

Use **uv**, with dependencies in standard `pyproject.toml` fields and the lock in `uv.lock`.

- One tool for creating the venv, resolving, locking and running commands.
- Much faster than pip or Poetry, which matters on every CI run and Docker build.
- `uv sync --locked` fails if the lockfile is out of date, so CI and the image always build exactly what was reviewed.
- Dependency groups (`[dependency-groups]`, PEP 735) keep dev tools out of the production image.

## Consequences

- Contributors need uv installed (`brew install uv` or the official installer).
- The Dockerfile copies the `uv` binary from its official image, pinned to a version, into the build stage only. The runtime image has just the virtualenv.

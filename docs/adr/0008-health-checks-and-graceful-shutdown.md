# 8. Health checks and graceful shutdown

- Status: accepted
- Date: 2026-10-26

## Context

Kubernetes uses probes to decide whether to restart a pod (liveness) and whether to send it traffic (readiness). Getting them wrong causes outages: a liveness check that queries the database makes Kubernetes restart every pod during a brief database blip, which turns a small incident into a full outage. Deploys and node drains also drop requests unless shutdown is handled carefully.

## Decision

**Probes**

- `/livez` only proves the process can serve HTTP. It never checks dependencies.
- `/readyz` checks the database with `SELECT 1` and a short timeout, and returns `503` if it fails. The pod leaves the load balancer until the database is back, without restarting.
- A `startupProbe` on `/livez` gives slow starts time without loosening the liveness probe.

**Shutdown sequence**

1. Kubernetes marks the pod as terminating and starts removing it from Service endpoints. This propagates asynchronously.
2. A `preStop` **sleep** (5s) keeps the pod serving while that happens, so new requests aren't sent to a closed socket. It uses the native `sleep` lifecycle action (Kubernetes 1.30+), so the image doesn't need a shell.
3. SIGTERM goes to `python` (PID 1, exec-form `CMD`). uvicorn stops accepting connections and drains in-flight requests for up to `APP_SHUTDOWN_TIMEOUT_SECONDS` (20s).
4. The lifespan shutdown closes the connection pool and flushes pending spans.
5. Kubernetes sends SIGKILL at `terminationGracePeriodSeconds` (30s), which is longer than the sleep plus the drain.

Rollouts use `maxUnavailable: 0`, and a PodDisruptionBudget keeps one replica up during node drains.

## Consequences

- The three timeouts are linked. The chart's `values.yaml` documents the rule: preStop sleep + drain < grace period.
- Long-lived connections (websockets, streaming) would need their own drain handling.

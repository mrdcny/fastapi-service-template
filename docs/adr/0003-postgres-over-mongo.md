# 3. PostgreSQL over MongoDB

- Status: accepted
- Date: 2026-10-26

## Context

Most services built from this template will store business records with relationships between them (users, orders, line items), need transactions across several rows, and need ad-hoc queries for support and reporting. We need one default datastore.

## Decision

Use **PostgreSQL**.

- Relational data with constraints (foreign keys, unique, check) catches bugs at write time instead of in a later read.
- Multi-row ACID transactions are the default, not a feature to opt into.
- `jsonb` covers the cases where a document model really is the better fit, with indexing, so we don't lose MongoDB's main strength.
- Every major cloud offers it managed (RDS, Cloud SQL, Azure Database), and the operational knowledge is widespread.
- Schema migrations (ADR 6) make change explicit and reviewable rather than implicit in application code.

MongoDB would fit better for genuinely schemaless, document-shaped data with little cross-document querying. That's not the common case for a service template.

## Consequences

- Every schema change needs a migration.
- Horizontal write scaling needs more work (partitioning, Citus) than it would with MongoDB sharding. For most services a single primary with read replicas is plenty.

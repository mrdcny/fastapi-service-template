# 1. Record architecture decisions

- Status: accepted
- Date: 2026-10-26

## Context

A template is only useful if people understand why it looks the way it does. Without the reasoning, every choice reads as arbitrary and gets "fixed" by the next person who copies it.

## Decision

Record each significant decision as a short Markdown file in `docs/adr/`, numbered in order, using the format from Michael Nygard's [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions): context, decision, consequences. Each one should take about a minute to read.

ADRs are never edited after they're accepted except to change their status. A reversal is a new ADR that supersedes the old one.

## Consequences

- Reviewers and future readers can see the trade-offs, not just the outcome.
- Changing a recorded decision means writing down why, which is a small cost.

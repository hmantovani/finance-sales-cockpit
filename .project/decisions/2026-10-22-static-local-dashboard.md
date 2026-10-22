---
date: 2026-10-22
agent: codex
---

## Context

The first release needs a reviewable browser dashboard and trustworthy data calculations inside a local-only project repository.

## Decision

Build a static HTML/CSS/JavaScript dashboard served locally, backed by deterministic Python-generated JSON. Use SQLite in the validation script for relationship checks and source reconciliation. Fix the demonstration snapshot at 2026-10-22.

## Why

The dashboard runs without a dependency installation, while the generation and SQL checks demonstrate a transparent data pipeline. A fixed snapshot makes portfolio screenshots and test results repeatable.

## Consequences

The app has no live data integration. Product selection limits sales only because payments and receivables are invoice-level facts. The local Git repository remains without a remote.

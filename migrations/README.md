# MIGRATIONS

This folder is reserved for future compatibility migrations.

Typical uses:
- rewrite old AQUA config keys into new env names
- convert stored metadata formats
- migrate dashboard helper caches or artifacts

Rule:
- migrations must be idempotent
- migrations must be documented
- migrations must never mutate OpenClaw core files unless explicitly required

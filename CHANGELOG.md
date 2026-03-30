# Changelog

## Unreleased

Post-`v0.1.0` hardening and portability updates.

Highlights:
- removed VPS-specific hostnames, ports, and SSH details from runtime defaults
- added `.env` keys for public URL and OpenClaw tunnel helper output
- made `install.sh` print concrete login URLs after install
- auto-generated `AQUA_SECRET_KEY` on first install
- added `FIRST_RUN.md` and clarified long-term upgrade steps
- kept the default login password aligned with the requested first-run baseline
- made OpenClaw helper output derive from current host or `.env` instead of one hardcoded VPS

## 0.1.0 - 2026-03-30

Initial package-managed release of AQUA Manager ClawBot.

Highlights:
- extracted dashboard into a standalone companion package
- moved runtime configuration to `.env`
- added install, update, doctor, smoke-test, package-release, and rollback scripts
- hardened restore/upload/delete path handling
- added OpenClaw access helper caching
- switched production deployment to `waitress`
- documented install, upgrade, compatibility, backup, restore, rollback, and publishing

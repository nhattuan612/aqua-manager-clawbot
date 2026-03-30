# Changelog

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

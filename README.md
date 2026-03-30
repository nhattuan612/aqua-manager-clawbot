# AQUA Manager ClawBot

AQUA Manager ClawBot is an operational dashboard that sits next to OpenClaw instead of modifying OpenClaw itself.

That design is intentional:
- easier to move to another VPS
- easier to upgrade OpenClaw without forking its UI
- easier to restore after incidents
- easier to document and automate

## Package layout
- `app/`: Flask backend + templates
- `config/`: example environment file
- `deploy/`: install, update, rollback, doctor, smoke-test, PM2 launcher
- `docs/`: installation, upgrade, backup/restore, rollback, compatibility notes
- `migrations/`: reserved for future config/data migrations

## Quick start
```bash
cd aqua-manager-clawbot
bash deploy/install.sh
```

Then edit `.env` in the install directory and reload:
```bash
pm2 restart aqua_manager_clawbot --update-env
```

`deploy/install.sh` prints the login URLs right after first install so operators
know exactly where to access the dashboard on the new VPS.

For production-like VPS use, the package launcher prefers `waitress` from the
virtualenv. That keeps AQUA Manager stable under PM2 without modifying
OpenClaw.

## Operating model
- OpenClaw remains a separate system.
- AQUA reads OpenClaw state and workspace files.
- OpenClaw gateway access uses `SSH tunnel + tokenized URL`.
- AQUA does not rely on patching OpenClaw internals for normal operations.

Read the full docs in:
- [INSTALL](./docs/INSTALL.md)
- [FIRST_RUN](./docs/FIRST_RUN.md)
- [UPGRADE](./docs/UPGRADE.md)
- [BACKUP_RESTORE](./docs/BACKUP_RESTORE.md)
- [ROLLBACK](./docs/ROLLBACK.md)
- [COMPATIBILITY](./docs/COMPATIBILITY.md)
- [RELEASE_CHECKLIST](./docs/RELEASE_CHECKLIST.md)
- [PUBLISHING](./docs/PUBLISHING.md)

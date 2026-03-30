# UPGRADE

## Design rule
Upgrade AQUA independently from OpenClaw whenever possible.

## Safe upgrade flow
1. Backup current install:
   ```bash
   bash deploy/update.sh
   ```
2. The script saves a snapshot before overwriting files.
3. Dependencies are refreshed in `.venv`.
4. PM2 reloads the app.
5. `doctor` and `smoke-test` run after reload.

## Exact operator flow
When coming back months or years later, use the same sequence:

1. Go to the install directory
   ```bash
   cd ~/.aqua-manager-clawbot
   ```
2. Save or verify `.env`
3. Update package files
   - if installed from git:
     ```bash
     git pull --ff-only origin main
     ```
   - if installed from a release tarball:
     download the new release, extract it, and run `bash deploy/install.sh`
4. Run:
   ```bash
   bash deploy/update.sh
   ```
5. Check:
   ```bash
   bash deploy/doctor.sh
   bash deploy/smoke-test.sh
   ```
6. If anything looks wrong, roll back immediately with the newest snapshot

This keeps upgrades repeatable even if the original chat context is long gone.

## OpenClaw upgrades
AQUA is designed to survive OpenClaw upgrades because:
- it reads workspace/config state
- it does not patch the OpenClaw UI
- it treats OpenClaw access as `tunnel + tokenized URL`

If OpenClaw changes CLI or config schema, update the compatibility layer in AQUA rather than forking OpenClaw.

## Recommended rule
Before upgrading OpenClaw:
1. backup OpenClaw workspace
2. backup AQUA `.env`
3. run `doctor`
4. upgrade OpenClaw
5. run `doctor` again
6. if needed, update AQUA compatibility notes/scripts

## Rollback rule
If the upgrade behaves badly:
1. use the newest snapshot in `.update-snapshots/`
2. run:
   ```bash
   bash deploy/rollback.sh /path/to/snapshot
   ```
3. run `smoke-test` again before reopening public access

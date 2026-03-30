# ROLLBACK

## Goal
Return AQUA Manager to a previous known-good state after a bad upgrade or a bad configuration change.

## Snapshot types
- install/update snapshots inside `~/.aqua-manager-clawbot/.update-snapshots/`
- manual/live snapshots inside `~/.aqua-manager-snapshots/`

## Fast rollback with the script
```bash
bash deploy/rollback.sh /home/ubuntu/.aqua-manager-clawbot/.update-snapshots/<STAMP>
```

The script restores:
- `app/`
- `config/`
- `deploy/`
- `docs/`
- `migrations/`
- `requirements.txt`
- `README.md`
- `VERSION`
- optional `.env` if it exists inside the snapshot

Then it recreates dependencies, restarts PM2, waits for `/login`, and runs `doctor`.

## Manual rollback
1. stop or reload the PM2 app
2. copy the snapshot files back into `~/.aqua-manager-clawbot`
3. restore `.env` if needed
4. run:
   ```bash
   bash deploy/doctor.sh
   bash deploy/smoke-test.sh
   ```

## Recommended rule
- snapshot before every OpenClaw upgrade
- snapshot before every AQUA upgrade
- keep at least one known-good snapshot from the previous release

# BACKUP_RESTORE

## What to back up
For AQUA itself:
- install directory
- `.env`
- `.venv` is optional, because it can be recreated

For OpenClaw:
- `~/.openclaw`
- workspace data
- PM2 or systemd service definitions if customized

## Recommended minimum AQUA backup
```bash
tar -czf aqua-manager-backup.tar.gz \
  ~/.aqua-manager-clawbot/.env \
  ~/.aqua-manager-clawbot/app \
  ~/.aqua-manager-clawbot/deploy \
  ~/.aqua-manager-clawbot/config
```

## Restore strategy
1. reinstall package files
2. restore `.env`
3. recreate `.venv`
4. run `doctor`
5. run `smoke-test`
6. restart PM2

## Snapshot-based rollback
For application-only incidents, prefer the built-in rollback path instead of a
full manual restore:
```bash
bash deploy/rollback.sh /home/ubuntu/.aqua-manager-clawbot/.update-snapshots/<STAMP>
```

## Why restore safety was tightened
ZIP restore now validates paths and ensures restored files stay inside the configured restore root. This prevents archive path traversal and makes restore behavior predictable across future VPS migrations.

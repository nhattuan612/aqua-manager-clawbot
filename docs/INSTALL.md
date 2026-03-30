# INSTALL

## Goal
Install AQUA Manager on a VPS as a companion app for an existing OpenClaw setup.

## Preconditions
- Python 3 available
- PM2 available
- OpenClaw already installed
- OpenClaw workspace available

## Recommended install flow
1. Copy or clone this package to the VPS.
2. Run:
   ```bash
   bash deploy/install.sh
   ```
3. Edit the generated `.env`.
4. Re-run:
   ```bash
   bash deploy/doctor.sh
   bash deploy/smoke-test.sh
   ```

## Install from a release tarball
```bash
tar -xzf aqua-manager-clawbot-0.1.0.tar.gz
cd aqua-manager-clawbot
bash deploy/install.sh
```

## Important `.env` values
- `AQUA_ADMIN_PASSWORD`
- `AQUA_SECRET_KEY`
- `AQUA_OPENCLAW_HOME`
- `AQUA_WORKSPACE_DIR`
- `AQUA_OPENCLAW_BIN`
- `AQUA_PM2_BIN`
- `AQUA_GATEWAY_URL`

## Why `.env` matters
The code does not hardcode one specific VPS layout anymore. If a future VPS uses:
- a different username
- a different OpenClaw home
- a different PM2 binary path
- a different dashboard port

you only adjust `.env`, not the source code.

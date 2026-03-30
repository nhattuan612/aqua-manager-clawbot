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
3. `install.sh` creates `.env` if it does not exist yet and auto-generates a random `AQUA_SECRET_KEY`.
4. At minimum, set:
   - `AQUA_ADMIN_PASSWORD`
   - `AQUA_PUBLIC_BASE_URL`
   - `AQUA_OPENCLAW_HOME`
   - `AQUA_OPENCLAW_BIN`
   - `AQUA_PM2_BIN`
5. Re-run:
   ```bash
   bash deploy/doctor.sh
   bash deploy/smoke-test.sh
   ```
6. Open the login link printed by `install.sh`.

## Install from a release tarball
```bash
tar -xzf aqua-manager-clawbot-0.1.0.tar.gz
cd aqua-manager-clawbot
bash deploy/install.sh
```

## Important `.env` values
- `AQUA_ADMIN_PASSWORD`
- `AQUA_SECRET_KEY`
- `AQUA_PUBLIC_BASE_URL`
- `AQUA_OPENCLAW_HOME`
- `AQUA_WORKSPACE_DIR`
- `AQUA_OPENCLAW_BIN`
- `AQUA_PM2_BIN`
- `AQUA_GATEWAY_URL`
- `AQUA_SSH_HOST`
- `AQUA_SSH_USER`
- `AQUA_SSH_PORT`

## Access after install
`install.sh` prints the URLs that operators need right away:
- local login URL: `http://127.0.0.1:<AQUA_PORT>/login`
- server IP login URL when detectable
- public login URL when `AQUA_PUBLIC_BASE_URL` is configured

The dashboard login password is stored in `.env` as `AQUA_ADMIN_PASSWORD`.
On first install, `AQUA_SECRET_KEY` is generated automatically.

## Why `.env` matters
The code does not hardcode one specific VPS layout anymore. If a future VPS uses:
- a different username
- a different OpenClaw home
- a different PM2 binary path
- a different dashboard port

you only adjust `.env`, not the source code.

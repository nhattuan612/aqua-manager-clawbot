# FIRST RUN

## Goal
Help a new operator reach the dashboard immediately after a fresh install.

## What `install.sh` already prints
- local login URL
- server IP login URL when the VPS can detect one
- public login URL when `AQUA_PUBLIC_BASE_URL` is configured

## Minimum first-run checklist
1. Open `.env`
2. Confirm these values:
   - `AQUA_ADMIN_PASSWORD`
   - `AQUA_PUBLIC_BASE_URL`
   - `AQUA_OPENCLAW_HOME`
   - `AQUA_OPENCLAW_BIN`
   - `AQUA_PM2_BIN`
   - `AQUA_SECRET_KEY` was auto-generated and is no longer the placeholder
3. Run:
   ```bash
   bash deploy/doctor.sh
   bash deploy/smoke-test.sh
   ```
4. Open `/login` using one of the printed URLs.

## OpenClaw access model
AQUA does not patch OpenClaw.

Use:
- AQUA Dashboard for management
- SSH tunnel + tokenized URL for OpenClaw control UI

That model is safer for future OpenClaw upgrades because the dashboard stays a
companion layer instead of modifying the OpenClaw frontend.

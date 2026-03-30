# COMPATIBILITY

## Supported model
AQUA Manager is built for the following operational contract:
- OpenClaw exists as a separate installation
- OpenClaw gateway is reachable locally
- OpenClaw workspace files are readable
- PM2 is available for process inspection

## Stable assumptions
- OpenClaw gateway may change UI implementation
- OpenClaw dashboard may change WebSocket/auth behavior
- OpenClaw config schema may evolve

Because of that, AQUA avoids depending on:
- direct UI patching of OpenClaw
- iframe-based full control access as a primary workflow
- hardcoded one-host path assumptions

## Compatibility boundary
AQUA should remain compatible as long as:
- `openclaw dashboard --no-open` still returns a tokenized URL
- workspace structure is broadly similar
- process state remains observable via PM2

If one of those changes, update the adapter logic in AQUA rather than modifying OpenClaw itself.

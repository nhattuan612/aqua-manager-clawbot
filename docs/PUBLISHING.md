# PUBLISHING

## Recommended publishing model

Publish AQUA Manager as:
1. a dedicated Git repository
2. versioned release tags
3. release tarballs created by `deploy/package-release.sh`

That gives two stable entry points:
- source history for engineers
- predictable release artifacts for operators

## Suggested release flow
1. update `VERSION`
2. update docs/changelog
3. create archive:
   ```bash
   bash deploy/package-release.sh
   ```
   This creates both the tarball and a `.sha256` checksum file.
4. create git tag, for example:
   ```bash
   git tag v0.1.0
   ```
5. attach the archive from `dist/` to the release

If the repository is hosted on GitHub, the included workflow can also rebuild
the tarball and checksum automatically when a `v*` tag is pushed.

## What to publish with every release
- source archive
- checksum file
- `INSTALL.md`
- `UPGRADE.md`
- `COMPATIBILITY.md`
- a short changelog

## What not to publish
- `.env`
- live secrets
- `.venv`
- VPS-specific backups

## Why this matters
If AQUA Manager is later used on another VPS or a different OpenClaw host, the
operator should be able to:
- download one release package
- edit one `.env`
- run one install command

without reverse-engineering your current production setup.

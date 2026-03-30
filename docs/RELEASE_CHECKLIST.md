# RELEASE_CHECKLIST

## Before tagging
1. update `VERSION`
2. update `CHANGELOG.md`
3. review `docs/COMPATIBILITY.md`
4. run:
   ```bash
   python3 -m py_compile app/app.py
   bash deploy/doctor.sh || true
   bash deploy/package-release.sh
   ```
5. confirm the package archive is created in `dist/`
6. confirm the checksum file is created next to the archive

## Suggested git flow
```bash
git status
git add .
git commit -m "release: v0.1.0"
git tag v0.1.0
```

## Release payload
- source repo/tag
- release tarball from `dist/`
- checksum file from `dist/`
- docs from `docs/`

## After publishing
1. test install from the release tarball on a staging VPS
2. run `doctor`
3. run `smoke-test`
4. only then promote to production

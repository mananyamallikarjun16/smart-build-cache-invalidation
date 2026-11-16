# Smart Build-Cache Invalidation

This Python project demonstrates a small content-addressed cache. A cache entry
is reused only when its key and the SHA-256 fingerprint of every declared input
and dependency still match. Editing a tracked dependency automatically causes a
cache miss and rebuild.

## Requirements and setup

- Python 3.10 or newer
- Git (only needed to publish the repository)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run and test

```powershell
python scripts\demo.py
python -m pytest -v
```

Run the demo twice: the first run prints `MISS` and builds; the next run prints
`HIT` without invoking the builder. Change `sample\message.txt` and run again to
see automatic invalidation. The demo cache is stored in the ignored `.cache`
folder.

## Design

- `smartcache/cache.py` hashes file names and bytes with SHA-256, tracks explicit
  module-to-file dependencies, validates the stored fingerprint, and atomically
  replaces JSON cache entries.
- `scripts/demo.py` is an executable example.
- `tests/test_cache.py` checks repeat hits, dependency invalidation, and missing
  input reporting.
- `.github/workflows/ci.yml` installs dependencies and runs pytest on pushes
  and pull requests using Python 3.12.

## GitHub Actions

The workflow checks out the commit, installs Python 3.12 and `requirements.txt`,
then runs `python -m pytest -v`. Pytest exits non-zero on failure, so GitHub
shows a red failed check and its test output; passing tests produce a green
check. To demonstrate failure safely, temporarily change the expected result in
`tests/test_cache.py` to an incorrect value, commit and push that change, then
open **Actions → Python CI → the failed run → test** to inspect the assertion.
Restore the correct assertion in a new commit and push; the next run should be
green after it completes.

## GitHub repository

```powershell
git push -u origin main
```

Public repository: https://github.com/mananyamallikarjun16/smart-build-cache-invalidation

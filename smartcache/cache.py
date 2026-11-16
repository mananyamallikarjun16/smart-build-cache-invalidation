"""A small content-addressed cache for build-like Python tasks."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


@dataclass(frozen=True)
class CacheResult:
    """Value returned by a cache lookup or rebuild."""

    value: Any
    cache_hit: bool
    fingerprint: str


class BuildCache:
    """Cache JSON-serializable build results based on source contents."""

    def __init__(self, cache_dir: str | Path) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _fingerprint(
        inputs: Iterable[str | Path],
        dependencies: Mapping[str, Iterable[str | Path]],
    ) -> str:
        files: dict[str, Path] = {}
        for path in inputs:
            resolved = Path(path).resolve()
            files[resolved.as_posix()] = resolved
        for module, paths in dependencies.items():
            for path in paths:
                resolved = Path(path).resolve()
                files[f"{module}:{resolved.as_posix()}"] = resolved

        digest = hashlib.sha256()
        for label, path in sorted(files.items()):
            if not path.is_file():
                raise FileNotFoundError(f"Cache input does not exist: {path}")
            digest.update(label.encode("utf-8"))
            digest.update(b"\0")
            with path.open("rb") as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
            digest.update(b"\0")
        return digest.hexdigest()

    def get_or_build(
        self,
        key: str,
        inputs: Iterable[str | Path],
        builder: Callable[[], Any],
        dependencies: Mapping[str, Iterable[str | Path]] | None = None,
    ) -> CacheResult:
        """Return a cached value, rebuilding whenever any tracked file changes."""
        fingerprint = self._fingerprint(inputs, dependencies or {})
        entry_id = hashlib.sha256(key.encode("utf-8")).hexdigest()
        entry_path = self.cache_dir / f"{entry_id}.json"

        try:
            entry = json.loads(entry_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            entry = None
        except json.JSONDecodeError:
            entry = None
        if (
            isinstance(entry, dict)
            and entry.get("key") == key
            and entry.get("fingerprint") == fingerprint
            and "value" in entry
        ):
            return CacheResult(entry["value"], True, fingerprint)

        value = builder()
        payload = json.dumps(
            {"key": key, "fingerprint": fingerprint, "value": value},
            indent=2,
            sort_keys=True,
        )
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.cache_dir,
                delete=False,
            ) as temporary:
                temporary.write(payload)
                temporary_path = temporary.name
            os.replace(temporary_path, entry_path)
        finally:
            if temporary_path and os.path.exists(temporary_path):
                os.unlink(temporary_path)
        return CacheResult(value, False, fingerprint)

from pathlib import Path

import pytest

from smartcache import BuildCache


def test_cache_hit_skips_builder_and_source_change_invalidates(tmp_path: Path) -> None:
    source = tmp_path / "source.py"
    dependency = tmp_path / "dependency.py"
    source.write_text("value = 1\n", encoding="utf-8")
    dependency.write_text("constant = 2\n", encoding="utf-8")
    cache = BuildCache(tmp_path / "cache")
    calls = 0

    def build() -> dict[str, int]:
        nonlocal calls
        calls += 1
        return {"built": calls}

    first = cache.get_or_build(
        "compile",
        [source],
        build,
        dependencies={"library": [dependency]},
    )
    second = cache.get_or_build(
        "compile",
        [source],
        build,
        dependencies={"library": [dependency]},
    )
    assert not first.cache_hit
    assert second.cache_hit
    assert calls == 1

    dependency.write_text("constant = 3\n", encoding="utf-8")
    third = cache.get_or_build(
        "compile",
        [source],
        build,
        dependencies={"library": [dependency]},
    )
    assert not third.cache_hit
    assert calls == 2


def test_missing_input_is_reported(tmp_path: Path) -> None:
    cache = BuildCache(tmp_path / "cache")
    with pytest.raises(FileNotFoundError, match="Cache input"):
        cache.get_or_build("compile", [tmp_path / "missing.py"], lambda: None)

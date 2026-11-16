"""Run a repeatable demonstration of cache hits and invalidation."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from smartcache import BuildCache


def main() -> None:
    source = ROOT / "sample" / "message.txt"
    cache = BuildCache(ROOT / ".cache")
    dependencies = {"sample-message": [source]}

    def build() -> dict[str, str]:
        print("BUILD RUN: reading the source file")
        return {"message": source.read_text(encoding="utf-8").strip().upper()}

    result = cache.get_or_build(
        "sample-uppercase-v1",
        [source],
        build,
        dependencies=dependencies,
    )
    print(f"Cache {'HIT' if result.cache_hit else 'MISS'}")
    print(f"Result: {result.value['message']}")
    print(f"Fingerprint: {result.fingerprint}")


if __name__ == "__main__":
    main()

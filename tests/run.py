"""pytest 없이 tests/를 실행하는 내장 러너.

    python3 tests/run.py

test_*.py 안의 test_* 함수를 모두 찾아 실행하고 요약을 출력한다.
pytest가 있으면 `python3 -m pytest tests/`를 권장.
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    import tests

    passed = failed = 0
    failures = []
    for mod in pkgutil.iter_modules(tests.__path__, "tests."):
        if not mod.name.rsplit(".", 1)[-1].startswith("test_"):
            continue
        module = importlib.import_module(mod.name)
        for attr in sorted(dir(module)):
            if not attr.startswith("test_"):
                continue
            fn = getattr(module, attr)
            if not callable(fn):
                continue
            try:
                fn()
                passed += 1
            except Exception as e:  # noqa: BLE001
                failed += 1
                failures.append((f"{mod.name}.{attr}", e, traceback.format_exc()))

    print(f"\n{'='*56}")
    for name, e, tb in failures:
        print(f"✗ {name}: {type(e).__name__}: {e}")
        print(tb)
    print(f"{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

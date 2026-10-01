#!/usr/bin/env python3
"""One-time compatibility adjustments for exact cross-version Ninja checkpoints."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

AGE_NS = 946684800 * 10**9
M154_AUXILIARY_SEARCH_TURBINE = Path(
    "obj/chrome/browser/auxiliary_search/java.turbine.jar"
)
M154_AUXILIARY_SEARCH_MARKER = ".kiwi-m154-auxiliary-search-deps-invalidated"


def invalidate_m154_auxiliary_search_cycle(out: Path) -> bool:
    """Invalidate the one M153 turbine output whose recorded dependency reversed in M154.

    Chromium M153 made auxiliary_search:java depend on magic_stack:java. M154 moved the
    module classes into module_java and made magic_stack:java depend on
    auxiliary_search:java. An exact M153 checkpoint can therefore retain the removed edge
    in .ninja_deps and combine it with the new edge into a cycle. Changing only the old
    turbine jar mtime makes Ninja ignore that stale dependency record and rebuild the jar;
    no cache files, dependency logs, objects, or generated outputs are deleted.
    """
    out = Path(out)
    marker = out / M154_AUXILIARY_SEARCH_MARKER
    if marker.exists():
        return False
    turbine = out / M154_AUXILIARY_SEARCH_TURBINE
    if not turbine.is_file():
        return False
    os.utime(turbine, ns=(AGE_NS, AGE_NS))
    marker.write_text("M153 auxiliary_search:java dependency invalidated for M154\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    changed = invalidate_m154_auxiliary_search_cycle(args.out)
    print(
        "Invalidated the stale M153 auxiliary_search turbine dependency."
        if changed
        else "No M153 auxiliary_search turbine invalidation was needed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

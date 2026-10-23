#!/usr/bin/env python3
"""Repair a single proven M156 Chromium/Vanadium Java GN dependency cycle.

Never touch out/Default, cache state, generated files, source outside base/BUILD.gn.
Fail closed on unknown upstream versions or unexpected source structure.
"""
import argparse
import hashlib
import json
from pathlib import Path

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def target_block(src: str, target: str):
    marker = f'android_library("{target}") {{'
    if src.count(marker) != 1:
        raise RuntimeError(f"Expected exactly one GN target: {target}")
    start = src.index(marker)
    # This is an Android GN android_library stanza with no nested declarations.
    end = src.find("\n  }\n", start)
    if end < 0 or end-start > 16000:
        raise RuntimeError("Malformed or unexpected GN target block: "+target)
    return start, end, src[start:end]

def repair(tree: Path):
    base=tree/"base/BUILD.gn"
    version=tree/"base/version_info/android/BUILD.gn"
    original=base.read_bytes()
    txt=original.decode("utf-8")
    vs=version.read_text(encoding="utf-8")
    _,_,base_block=target_block(txt,"base_java")
    _,_,ver_block=target_block(vs,"version_constants_java")
    if '":build_info_java"' not in base_block:
        raise RuntimeError("M156 base_java no longer public-depends on build_info_java")
    if '"//base:base_java"' not in ver_block:
        raise RuntimeError("M156 version_constants_java no longer depends on base_java")

    begin,end,build=target_block(txt,"build_info_java")
    bad='"//base/version_info/android:version_constants_java",'
    good='"//base/version_info/android:channel_enum_java",'
    if build.count(bad)==1 and good not in build:
        new_build=build.replace(bad,good,1)
        result=txt[:begin]+new_build+txt[end:]
        if result.replace(new_build,build,1)!=txt:
            raise RuntimeError("unexpected additional change to base GN")
        fixed=result.encode("utf-8")
        base.write_bytes(fixed)
        status="fixed"
    elif build.count(good)==1 and bad not in build:
        # Upstream already corrected it: do not silently apply an unrelated workaround.
        raise RuntimeError("GN build_info_java already uses channel_enum_java; cycle has another cause")
    else:
        raise RuntimeError("Unknown build_info_java dependency state; refusing blind GN edit")
    return {
      "version":"156.0.8078.47",
      "source":"base/BUILD.gn",
      "status":status,
      "before_sha256":sha(original),
      "after_sha256":sha(fixed),
      "version_info_build_sha256":sha(version.read_bytes()),
      "before_dependency":bad,
      "after_dependency":good,
      "reason":"prevent build_info -> version_constants -> base_java -> build_info cycle"
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("chromium_source",type=Path)
    parser.add_argument("report",type=Path)
    args=parser.parse_args()
    args.report.parent.mkdir(parents=True,exist_ok=True)
    result=repair(args.chromium_source.resolve())
    args.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("KIWI_M156_JAVA_GN_CYCLE_FIX "+json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Build an isolated M156 patch-rebase candidate from verified GitHub audit sources.
No compilation, repository push, cache writes, or old release alterations.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[1]
PORT = ROOT / "kiwi_port"
AUDIT = Path(os.environ["RUNNER_TEMP"]) / "kiwi156-audit"
OUTPUT = ROOT / "output" / "kiwi156-rebase-candidate"
SRC = Path(os.environ["RUNNER_TEMP"]) / "kiwi156-rebase-src"
REPLAY = Path(os.environ["RUNNER_TEMP"]) / "kiwi156-strict-replay"
STATUS = OUTPUT / "results.json"
OUTPUT.mkdir(parents=True, exist_ok=True)
events = []
candidate = OUTPUT / "patches"
candidate.mkdir(parents=True, exist_ok=True)

def run(cmd, cwd=None, check=True):
    p = subprocess.run(list(map(str, cmd)), cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError("command failed: " + " ".join(map(str,cmd)) +
                           "\n" + (p.stdout + p.stderr)[-8000:])
    return p

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def archive_extract(target):
    target.mkdir(parents=True, exist_ok=True)
    archive = AUDIT / "kiwi-sources-before.tar.gz"
    with tarfile.open(archive, "r:gz") as inp:
        for member in inp.getmembers():
            dest = target / member.name
            if not dest.resolve().is_relative_to(target.resolve()) or not member.isfile():
                raise RuntimeError("unsafe or unexpected archive item: " + member.name)
        inp.extractall(target, filter="data")

def write_status(reason, done=False):
    STATUS.write_text(json.dumps({
        "status": "pass" if done else "incomplete",
        "reason": reason, "events": events
    }, indent=2, ensure_ascii=False)+"\n")

def main():
    rawhash = json.loads((AUDIT/"kiwi-source-hashes-before.json").read_text())
    if len(rawhash["files"]) != 99:
        raise RuntimeError("audit did not contain 99 tracked source hashes")
    if rawhash["chromium_commit"] != "5869fe313571d75152b77813cf0a4ee26a4e6df0":
        # The audit reporter carries stale manifest metadata (M155.84).
        events.append({"warning":"before hash JSON contains inherited M155 metadata; verify actual M156 source from run pins"})
    archive_extract(SRC)
    for rel,expected in rawhash["files"].items():
        actual=sha(SRC/rel)
        if actual != expected:
            raise RuntimeError("audit before source digest mismatch: " + rel)
    run(["git","init","-q"],cwd=SRC)
    run(["git","config","user.email","audit@localhost"],cwd=SRC)
    run(["git","config","user.name","Kiwi Audit"],cwd=SRC)
    run(["git","add","-A"],cwd=SRC)
    run(["git","commit","-q","--allow-empty","-m","Verified M156 before baseline"],cwd=SRC)
    series=json.loads((PORT/"patches/series.json").read_text())
    manifest=json.loads((PORT/"manifest.json").read_text())
    newseries={"format":1,"base":"post-Titanium a3e4b86339a8db237d95d8e8e78248c8f6a1df68","features":[]}
    problems=[]
    for feature in series["features"]:
        patch=PORT/"patches"/feature["patch"]
        before=run(["git","apply","--check",patch],cwd=SRC,check=False)
        if before.returncode==0:
            run(["git","apply","--whitespace=nowarn",patch],cwd=SRC)
            how="exact"
            detail=""
        else:
            trial=run(["patch","-d",SRC,"-p1","--batch","--forward","--fuzz=2","-i",patch],check=False)
            how="context-repair-attempt"
            detail=(trial.stdout+trial.stderr)[-9000:]
            rejects=[str(p.relative_to(SRC)) for p in SRC.rglob("*.rej")]
            if trial.returncode!=0 or rejects:
                events.append({"id":feature["id"],"result":"conflict","details":detail,"rejects":rejects})
                problems.append(feature["id"])
                break
        run(["git","add","-A"],cwd=SRC)
        changed=run(["git","diff","--cached","--name-only"],cwd=SRC).stdout.splitlines()
        if set(changed)!=set(feature["files"]):
            events.append({"id":feature["id"],"result":"file-set-mismatch","changed":changed,"expected":feature["files"],"details":detail})
            problems.append(feature["id"])
            break
        patch_text=run(["git","diff","--cached","--binary","--full-index"],cwd=SRC).stdout
        if not patch_text:
            raise RuntimeError("empty feature: "+feature["id"])
        generated=candidate/feature["patch"]
        generated.write_text(patch_text)
        feat=dict(feature)
        feat["sha256"]=sha(generated)
        newseries["features"].append(feat)
        events.append({"id":feature["id"],"result":"candidate","method":how,"detail":detail[:800]})
        run(["git","commit","-q","-m",feature["id"]],cwd=SRC)
    if problems:
        write_status("M156 context repair requires manual correction: " + ",".join(problems))
        raise RuntimeError("Stopped at first nonrecoverable feature; candidate saved for review")
    if len(newseries["features"]) != 25:
        raise RuntimeError("feature count not 25")
    for rel in manifest["files"]:
        if rel not in rawhash["files"]:
            raise RuntimeError("untracked source: "+rel)
        manifest["files"][rel]["before_sha256"]=rawhash["files"][rel]
        manifest["files"][rel]["after_sha256"]=sha(SRC/rel)
    manifest["titanium_commit"]="a3e4b86339a8db237d95d8e8e78248c8f6a1df68"
    manifest["vanadium_commit"]="2ae4335402eabcc6e025f3400185fe25094d8521"
    manifest["chromium_commit"]="1d17a2e2ee147bb7d6ae2ab6abdb3a2510c17775"
    manifest["chromium_version"]="156.0.8078.47"
    (OUTPUT/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    (candidate/"series.json").write_text(json.dumps(newseries,indent=2,ensure_ascii=False)+"\n")
    # Use only disposable runner checkout, then validate the regenerated series.
    # Original branch files and GitHub cache are never written.
    shutil.copy2(OUTPUT/"manifest.json",PORT/"manifest.json")
    for f in candidate.iterdir():
        shutil.copy2(f,PORT/"patches"/f.name)
    run(["python3",PORT/"verify_series.py"])
    archive_extract(REPLAY)
    run(["git","init","-q"],cwd=REPLAY)
    run(["python3",PORT/"apply.py",REPLAY])
    for rel,v in manifest["files"].items():
        if sha(REPLAY/rel)!=v["after_sha256"]:
            raise RuntimeError("strict replay post hash mismatch: "+rel)
    unit=run(["python3","-m","unittest",
              "kiwi_port.test_reapply","kiwi_port.test_incremental_sources",
              "kiwi_port.test_checkpoint_compat","kiwi_port.test_night_mode_patch",
              "kiwi_port.test_credentials_patch","kiwi_port.test_checkpoint_restore",
              "kiwi_port.test_job_budget"],cwd=ROOT,check=False)
    (OUTPUT/"unit-test-log.txt").write_text(unit.stdout+unit.stderr)
    if unit.returncode:
        raise RuntimeError("unit tests failed on candidate, see unit-test-log.txt")
    write_status("All 25 candidate patches strict-replay against actual M156 audited before files, 99 hashes match, unit tests pass",True)
    print("PASS: M156 candidate prepared. Review context repairs and compile constraints before production.")

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        (OUTPUT/"exception.txt").write_text(str(exc)+"\n"+traceback.format_exc())
        if not STATUS.exists(): write_status(str(exc))
        print("CANDIDATE INCOMPLETE: "+str(exc),file=sys.stderr)
        sys.exit(1)

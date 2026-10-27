#!/usr/bin/env python3
"""Copy skills from .agents/skills (source, read by Codex) to .claude/skills (read by Claude Code).

Edit skills only in .agents/skills, then run this script. Copies instead of symlinks so the
workflow still works when downloaded as a ZIP on Windows.

Usage:
  python3 scripts/sync_skills.py          # copy, remove skills deleted from the source
  python3 scripts/sync_skills.py --check  # exit 1 if .claude/skills is out of date
"""
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / ".agents" / "skills"
DST = ROOT / ".claude" / "skills"


def differences():
    if not DST.is_dir():
        return ["(chưa có .claude/skills)"]
    diffs = []

    def walk(cmp, rel=""):
        for name in cmp.left_only + cmp.right_only + cmp.diff_files + cmp.funny_files:
            diffs.append(f"{rel}{name}")
        for name, sub in cmp.subdirs.items():
            walk(sub, f"{rel}{name}/")

    walk(filecmp.dircmp(SRC, DST, ignore=[".DS_Store", "__pycache__"]))
    return diffs


def main():
    if not SRC.is_dir():
        sys.exit("Không thấy .agents/skills.")
    if "--check" in sys.argv[1:]:
        diffs = differences()
        if diffs:
            print(".claude/skills chưa khớp .agents/skills:", ", ".join(diffs))
            sys.exit(1)
        print("Khớp.")
        return
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
    names = sorted(p.name for p in DST.iterdir() if p.is_dir())
    print(f"Đã chép {len(names)} skill sang .claude/skills: {', '.join(names)}")


if __name__ == "__main__":
    main()

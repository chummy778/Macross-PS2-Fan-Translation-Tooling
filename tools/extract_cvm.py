#!/usr/bin/env python3
"""Unpack CRI CVM containers to a directory tree.

    python3 tools/extract_cvm.py <out_dir> <file.cvm> [more.cvm ...]

Each container is extracted to <out_dir>/<NAME>/ preserving inner paths.
Nothing here modifies the source: every container is opened read-only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from cvm import Cvm


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    out_root = sys.argv[1]
    for path in sys.argv[2:]:
        stem = os.path.splitext(os.path.basename(path))[0].upper()
        try:
            c = Cvm(path)
            files = c.files()
        except Exception as e:
            print(f"{stem}: skipped ({e})")
            continue
        n = 0
        for name, lba, length in files:
            dst = os.path.join(out_root, stem, name)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(c.read(lba, length))
            n += 1
        print(f"{stem}: {n} files -> {os.path.join(out_root, stem)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

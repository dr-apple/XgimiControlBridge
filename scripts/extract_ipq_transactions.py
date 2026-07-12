#!/usr/bin/env python3
"""Extract candidate IPq Binder transactions from MediaTek's NDK AIDL stub."""

from __future__ import annotations

import argparse
import re
import signal
import subprocess
import sys
from pathlib import Path


SYMBOL_RE = re.compile(r"^([0-9a-fA-F]+)\s+\w\s+aidl::vendor::mediatek::hardware::pq::BpPq::(.+)$")
TRANSACTION_RE = re.compile(r"\bmovs\s+r1,\s+#0x([0-9a-fA-F]+)")


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)


def find_objdump() -> str:
    candidates = [
        "/Library/Developer/CommandLineTools/usr/bin/llvm-objdump",
        "llvm-objdump",
        "objdump",
    ]
    for candidate in candidates:
        try:
            run([candidate, "--version"])
            return candidate
        except (OSError, subprocess.CalledProcessError):
            continue
    raise SystemExit("No llvm-objdump/objdump found")


def symbols(library: Path) -> list[tuple[int, str]]:
    out = run(["nm", "-D", "-C", str(library)])
    methods: list[tuple[int, str]] = []
    for line in out.splitlines():
        match = SYMBOL_RE.match(line)
        if not match:
            continue
        name = match.group(2)
        if name.startswith(("BpPq(", "~BpPq(", "getInterfaceHash", "getInterfaceVersion")):
            continue
        methods.append((int(match.group(1), 16), name))
    return sorted(methods)


def transaction_for(objdump: str, library: Path, start: int, stop: int) -> int | None:
    out = run(
        [
            objdump,
            "-d",
            "-C",
            "--triple=thumbv7-none-linux-android",
            str(library),
            f"--start-address=0x{start:x}",
            f"--stop-address=0x{stop:x}",
        ]
    )
    lines = out.splitlines()
    for index, line in enumerate(lines):
        if "AIBinder_transact" not in line:
            continue
        for previous in reversed(lines[max(0, index - 16) : index]):
            match = TRANSACTION_RE.search(previous)
            if match:
                return int(match.group(1), 16)
    return None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library", type=Path, help="vendor.mediatek.hardware.pq-V1-ndk.so")
    args = parser.parse_args(argv)

    methods = symbols(args.library)
    objdump = find_objdump()
    print("code_hex\tcode_dec\taddress\tmethod")
    for index, (address, name) in enumerate(methods):
        stop = methods[index + 1][0] if index + 1 < len(methods) else address + 0x220
        code = transaction_for(objdump, args.library, address, stop)
        if code is None:
            continue
        print(f"0x{code:02x}\t{code}\t0x{address:08x}\t{name}")
    return 0


if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    raise SystemExit(main(sys.argv[1:]))

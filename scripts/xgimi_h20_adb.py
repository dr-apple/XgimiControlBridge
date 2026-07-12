#!/usr/bin/env python3
"""Small ADB test harness for confirmed XGIMI H20 native calls."""

from __future__ import annotations

import argparse
import subprocess
import sys


FOCUS_SERVICE = "xgimi.hardware.gmpf.IProjectorFocusManager/default"


def adb(args: list[str], *, dry_run: bool) -> int:
    cmd = ["adb", "shell", *args]
    print("+", " ".join(cmd))
    if dry_run:
        return 0
    return subprocess.call(cmd)


def service_call(service: str, transaction: int, params: list[str], *, dry_run: bool) -> int:
    return adb(["service", "call", service, str(transaction), *params], dry_run=dry_run)


def autofocus(args: argparse.Namespace) -> int:
    return service_call(FOCUS_SERVICE, 3, ["i32", str(args.mode)], dry_run=args.dry_run)


def raw_service(args: argparse.Namespace) -> int:
    return service_call(args.service, args.transaction, args.params, dry_run=args.dry_run)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print the ADB call without executing it")
    sub = parser.add_subparsers(dest="command", required=True)

    focus = sub.add_parser("autofocus", help="Start the confirmed projector autofocus binder call")
    focus.add_argument("--mode", type=int, default=2, help="Known working value: 2")
    focus.set_defaults(func=autofocus)

    raw = sub.add_parser("service-call", help="Execute a raw Android service call")
    raw.add_argument("service")
    raw.add_argument("transaction", type=int)
    raw.add_argument("params", nargs="*")
    raw.set_defaults(func=raw_service)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

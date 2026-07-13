#!/usr/bin/env python3
"""Small ADB test harness for confirmed and candidate XGIMI H20 native calls."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys


FOCUS_SERVICE = "xgimi.hardware.gmpf.IProjectorFocusManager/default"
PQ_SERVICE = "vendor.mediatek.hardware.pq.IPq/default"
PQ_GET_HDR_TYPE_TRANSACTION = 0x3B
PQ_SET_HDR_TYPE_TRANSACTION = 0x8A
PQ_GET_GLOBAL_NON_AWARE_TRANSACTION = 0x36
PQ_SET_PQ_PARAMS_TRANSACTION = 0x9F
PQ_SET_PQ_PARAMS_BY_GLOBAL_TRANSACTION = 0xA0
BRIDGE_COMPONENT = "de.drapple.xgimi/.XgimiCommandReceiver"
ACTION_GET_EXT_PQ_SETTINGS = "de.drapple.xgimi.GET_EXT_PQ_SETTINGS"


def adb(args: list[str], *, dry_run: bool, serial: str | None = None) -> int:
    cmd = ["adb"]
    if serial:
        cmd.extend(["-s", serial])
    shell_command = " ".join(shlex.quote(arg) for arg in args)
    cmd.extend(["shell", shell_command])
    print("+", " ".join(shlex.quote(part) for part in cmd))
    if dry_run:
        return 0
    return subprocess.call(cmd)


def adb_output(args: list[str], *, serial: str | None = None) -> str:
    cmd = ["adb"]
    if serial:
        cmd.extend(["-s", serial])
    shell_command = " ".join(shlex.quote(arg) for arg in args)
    cmd.extend(["shell", shell_command])
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        output = err.output.strip()
        if output:
            print(output, file=sys.stderr)
        return ""


def service_call(
    service: str,
    transaction: int,
    params: list[str],
    *,
    dry_run: bool,
    serial: str | None = None,
) -> int:
    return adb(["service", "call", service, str(transaction), *params], dry_run=dry_run, serial=serial)


def service_call_output(
    service: str,
    transaction: int,
    params: list[str],
    *,
    serial: str | None = None,
) -> str:
    return adb_output(["service", "call", service, str(transaction), *params], serial=serial)


def service_call_decoded_output(
    service: str,
    transaction: int,
    params: list[str],
    *,
    serial: str | None = None,
) -> tuple[str, list[int]]:
    output = service_call_output(service, transaction, params, serial=serial)
    return output, parse_service_call_words(output)


def parse_service_call_words(output: str) -> list[int]:
    words: list[int] = []
    for token in output.replace("'", " ").replace(")", " ").split():
        if token.startswith("0x"):
            continue
        try:
            words.append(int(token, 16))
        except ValueError:
            continue
    return words


def decode_two_single_value_arrays(words: list[int]) -> tuple[int, int, int] | None:
    if len(words) < 5 or words[1] != 1 or words[3] != 1:
        return None
    return words[0], words[2], words[4]


def decode_single_string_array(words: list[int]) -> tuple[int, int, str] | None:
    if len(words) < 5 or words[1] != 1 or words[3] != 1:
        return None

    string_length = words[4]
    chars: list[str] = []
    for word in words[5:]:
        for shift in (0, 16):
            codepoint = (word >> shift) & 0xFFFF
            if codepoint:
                chars.append(chr(codepoint))
            if len(chars) >= string_length:
                return words[0], words[2], "".join(chars)
    return words[0], words[2], "".join(chars)


def autofocus(args: argparse.Namespace) -> int:
    return service_call(FOCUS_SERVICE, 3, ["i32", str(args.mode)], dry_run=args.dry_run, serial=args.serial)


def pq_get_hdr_type(args: argparse.Namespace) -> int:
    params = ["i32", str(args.pq_id), "i32", "0", "i32", "0"]
    if args.dry_run:
        return service_call(PQ_SERVICE, PQ_GET_HDR_TYPE_TRANSACTION, params, dry_run=True, serial=args.serial)
    output = service_call_output(PQ_SERVICE, PQ_GET_HDR_TYPE_TRANSACTION, params, serial=args.serial)
    if not output:
        return 1
    print(output.strip())
    words = parse_service_call_words(output)
    decoded = decode_two_single_value_arrays(words)
    if decoded:
        status, return_code, hdr_type = decoded
        print(f"decoded: status={status} return_code={return_code} hdr_type={hdr_type}")
    return 0


def pq_scan_hdr_type(args: argparse.Namespace) -> int:
    for pq_id in range(args.start, args.end + 1):
        params = ["i32", str(pq_id), "i32", "0", "i32", "0"]
        output = service_call_output(PQ_SERVICE, PQ_GET_HDR_TYPE_TRANSACTION, params, serial=args.serial)
        if not output:
            return 1
        words = parse_service_call_words(output)
        decoded = decode_two_single_value_arrays(words)
        if decoded:
            status, return_code, hdr_type = decoded
            print(f"pq_id={pq_id} status={status} return_code={return_code} hdr_type={hdr_type}")
        else:
            print(f"pq_id={pq_id} undecoded={output.strip()}")
    return 0


def pq_set_hdr_type(args: argparse.Namespace) -> int:
    params = ["i32", str(args.pq_id), "i32", str(args.hdr_type)]
    return service_call(PQ_SERVICE, PQ_SET_HDR_TYPE_TRANSACTION, params, dry_run=args.dry_run, serial=args.serial)


def pq_get_global_settings(args: argparse.Namespace) -> int:
    params = ["i32", "0", "i32", "0"]
    if args.dry_run:
        return service_call(
            PQ_SERVICE,
            PQ_GET_GLOBAL_NON_AWARE_TRANSACTION,
            params,
            dry_run=True,
            serial=args.serial,
        )

    output = service_call_output(PQ_SERVICE, PQ_GET_GLOBAL_NON_AWARE_TRANSACTION, params, serial=args.serial)
    if not output:
        return 1
    words = parse_service_call_words(output)
    decoded = decode_single_string_array(words)
    if not decoded:
        print(output.strip())
        return 0

    status, return_code, text = decoded
    print(f"decoded: status={status} return_code={return_code} json_length={len(text)}")
    if args.raw:
        print(text)
        return 0

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print(text)
        return 0

    for key in args.keys:
        print(f"{key}={data.get(key)}")
    return 0


def read_global_settings(serial: str | None) -> tuple[int, int, dict]:
    output, words = service_call_decoded_output(
        PQ_SERVICE,
        PQ_GET_GLOBAL_NON_AWARE_TRANSACTION,
        ["i32", "0", "i32", "0"],
        serial=serial,
    )
    decoded = decode_single_string_array(words)
    if not decoded:
        raise RuntimeError(f"Could not decode global PQ settings: {output.strip()}")

    status, return_code, text = decoded
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        raise RuntimeError(f"Could not parse global PQ JSON: {err}") from err
    if not isinstance(data, dict):
        raise RuntimeError("Global PQ settings payload is not a JSON object")
    return status, return_code, data


def parse_json_value(raw: str) -> object:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def pq_set_current_global(args: argparse.Namespace) -> int:
    status, return_code, data = read_global_settings(args.serial)
    print(f"read: status={status} return_code={return_code} keys={len(data)}")

    old_value = data.get(args.key)
    new_value = parse_json_value(args.value)
    data[args.key] = new_value
    payload = json.dumps(data, separators=(",", ":"))

    if args.dry_run:
        print(f"{args.key}: {old_value!r} -> {new_value!r}")
        print(payload)
        return 0

    output, words = service_call_decoded_output(
        PQ_SERVICE,
        PQ_SET_PQ_PARAMS_BY_GLOBAL_TRANSACTION,
        ["s16", payload],
        serial=args.serial,
    )
    print(output.strip())
    if len(words) >= 2:
        print(f"decoded: status={words[0]} return_code={words[1]}")
    print(f"{args.key}: {old_value!r} -> {new_value!r}")
    return 0


def pq_set_params(args: argparse.Namespace) -> int:
    payload = args.json
    transaction = (
        PQ_SET_PQ_PARAMS_BY_GLOBAL_TRANSACTION
        if args.global_params
        else PQ_SET_PQ_PARAMS_TRANSACTION
    )
    params = ["s16", payload] if args.global_params else ["i32", str(args.pq_id), "s16", payload]
    return service_call(PQ_SERVICE, transaction, params, dry_run=args.dry_run, serial=args.serial)


def bridge_get_ext_pq_settings(args: argparse.Namespace) -> int:
    params = [
        "am",
        "broadcast",
        "-n",
        BRIDGE_COMPONENT,
        "-a",
        ACTION_GET_EXT_PQ_SETTINGS,
    ]
    if args.dry_run:
        return adb(params, dry_run=True, serial=args.serial)
    output = adb_output(params, serial=args.serial)
    if not output:
        return 1
    print(output.strip())
    return 0


def raw_service(args: argparse.Namespace) -> int:
    return service_call(args.service, args.transaction, args.params, dry_run=args.dry_run, serial=args.serial)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print the ADB call without executing it")
    parser.add_argument("-s", "--serial", help="ADB serial, for example 192.168.0.223:5555")
    sub = parser.add_subparsers(dest="command", required=True)

    focus = sub.add_parser("autofocus", help="Start the confirmed projector autofocus binder call")
    focus.add_argument("--mode", type=int, default=2, help="Known working value: 2")
    focus.set_defaults(func=autofocus)

    hdr = sub.add_parser("pq-get-hdr-type", help="Read MediaTek PQ HDR type for a PQ id")
    hdr.add_argument("--pq-id", type=int, default=0, help="PQ stream id to query")
    hdr.set_defaults(func=pq_get_hdr_type)

    hdr_scan = sub.add_parser("pq-scan-hdr-type", help="Read MediaTek PQ HDR type for a range of PQ ids")
    hdr_scan.add_argument("--start", type=int, default=0)
    hdr_scan.add_argument("--end", type=int, default=8)
    hdr_scan.set_defaults(func=pq_scan_hdr_type)

    hdr_set = sub.add_parser("pq-set-hdr-type", help="Set MediaTek PQ HDR type for a PQ id")
    hdr_set.add_argument("--pq-id", type=int, required=True)
    hdr_set.add_argument("--hdr-type", type=int, required=True)
    hdr_set.set_defaults(func=pq_set_hdr_type)

    global_settings = sub.add_parser(
        "pq-get-global-settings",
        help="Read native MediaTek global/non-aware PQ settings JSON",
    )
    global_settings.add_argument("--raw", action="store_true", help="Print the full decoded JSON")
    global_settings.add_argument(
        "--keys",
        nargs="*",
        default=[
            "Picture_Mode",
            "Backlight",
            "Brightness",
            "Contrast",
            "Gamma",
            "Color_Temperature",
            "AI_PQ",
            "MJC_Effect",
            "Local_Contrast",
        ],
    )
    global_settings.set_defaults(func=pq_get_global_settings)

    pq_params = sub.add_parser("pq-set-params", help="Experimental MediaTek PQ JSON write")
    pq_params.add_argument("--pq-id", type=int, default=0)
    pq_params.add_argument("--global-params", action="store_true")
    pq_params.add_argument("json")
    pq_params.set_defaults(func=pq_set_params)

    pq_set_current = sub.add_parser(
        "pq-set-current-global",
        help="Read current global PQ JSON, change one key, and write the full JSON back",
    )
    pq_set_current.add_argument("key", help="PQ JSON key, for example Backlight")
    pq_set_current.add_argument("value", help="New value parsed as JSON when possible")
    pq_set_current.set_defaults(func=pq_set_current_global)

    ext_pq = sub.add_parser(
        "bridge-get-ext-pq-settings",
        help="Read MediaTek ExtService PQ settings through the bridge APK",
    )
    ext_pq.set_defaults(func=bridge_get_ext_pq_settings)

    raw = sub.add_parser("service-call", help="Execute a raw Android service call")
    raw.add_argument("service")
    raw.add_argument("transaction", type=int)
    raw.add_argument("params", nargs="*")
    raw.set_defaults(func=raw_service)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

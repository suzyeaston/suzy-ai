from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys

from . import __version__
from .events import timeline_event, utc_now
from .paths import ensure_home, home
from .registry import load_registry
from .server import serve
from .store import append_event, read_events


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="suzy-ai",
        description="SUZY//AI local-first intelligence core.",
    )
    parser.add_argument("--version", action="store_true")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Create private local SUZY//AI state directories.")
    sub.add_parser("doctor", help="Inspect the local runtime and optional AI tools.")
    sub.add_parser("apps", help="Show registered applications.")

    server = sub.add_parser("serve", help="Run the local event/timeline HTTP server.")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=7331)

    timeline = sub.add_parser("timeline", help="Read or write local timeline events.")
    timeline_sub = timeline.add_subparsers(dest="timeline_command")

    add = timeline_sub.add_parser("add")
    add.add_argument("--stream", default="world")
    add.add_argument("--kind", default="note")
    add.add_argument("--source", default="human")
    add.add_argument("--text", required=True)
    add.add_argument("--unit", default="iso8601")
    add.add_argument("--value")

    listing = timeline_sub.add_parser("list")
    listing.add_argument("--stream")

    return parser


def doctor() -> int:
    ensure_home()
    print("SUZY//AI doctor")
    print()
    print(f"platform       {platform.platform()}")
    print(f"machine        {platform.machine()}")
    print(f"python         {platform.python_version()}")
    print(f"private home   {home()}")
    print()

    optional = [
        ("ffmpeg", "media"),
        ("yt-dlp", "video ingest"),
        ("whisper-cli", "local speech"),
        ("llama-server", "local model runtime"),
        ("ollama", "optional model runtime"),
    ]

    for command, purpose in optional:
        location = shutil.which(command)
        state = location if location else "not installed"
        print(f"{command:<14} {state:<34} # {purpose}")

    print()
    print("Optional tools may be added as adapters. None are required for the v0.1 core.")
    return 0


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()

    if args.version:
        print(f"SUZY//AI {__version__}")
        return

    if args.command == "init":
        root = ensure_home()
        print(f"Initialized private SUZY//AI home: {root}")
        return

    if args.command == "doctor":
        raise SystemExit(doctor())

    if args.command == "apps":
        print(json.dumps(load_registry(), indent=2))
        return

    if args.command == "serve":
        ensure_home()
        if args.host not in ("127.0.0.1", "localhost", "::1"):
            print(
                "Refusing non-loopback bind in v0.1. "
                "SUZY//AI is local-first by default.",
                file=sys.stderr,
            )
            raise SystemExit(2)
        serve(args.host, args.port)
        return

    if args.command == "timeline":
        ensure_home()

        if args.timeline_command == "add":
            value = args.value
            if value is None and args.unit == "iso8601":
                value = utc_now()
            elif value is None:
                parser.error("--value is required unless --unit=iso8601")

            event = timeline_event(
                stream=args.stream,
                kind=args.kind,
                source=args.source,
                unit=args.unit,
                value=value,
                payload={"text": args.text},
            )
            append_event(event)
            print(json.dumps(event, indent=2))
            return

        if args.timeline_command == "list":
            print(json.dumps(read_events(args.stream), indent=2))
            return

    parser.print_help()


if __name__ == "__main__":
    main()

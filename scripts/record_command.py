#!/usr/bin/env python3
"""Run an explicit argv, recording stdout, stderr, exit status and local time."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time
from zoneinfo import ZoneInfo


def redact(text):
    text = re.sub(r"(https?://)[^\s/@]+:[^\s/@]+@", r"\1<redacted>@", text)
    return re.sub(r"(?i)([?&](?:token|key|secret|password|auth)=)[^\s&]+", r"\1<redacted>", text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
    if not argv:
        parser.error("missing command")
    args.run_dir.mkdir(parents=True, exist_ok=True)
    log = args.run_dir / (args.name + ".log")
    env = os.environ.copy()
    overrides = dict(item.split("=", 1) for item in args.env)
    env.update(overrides)
    event = {"name": args.name, "cwd": str(args.cwd.resolve()), "argv": argv,
             "command": shlex.join(argv), "environment_overrides": overrides,
             "started_at": dt.datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
             "log": log.name}
    started = time.monotonic()
    with log.open("x") as stream:
        stream.write(redact(json.dumps(event, ensure_ascii=False)) + "\n")
        stream.flush()
        try:
            proc = subprocess.Popen(argv, cwd=args.cwd, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, errors="replace")
            for line in proc.stdout:
                stream.write(redact(line))
                stream.flush()
            status = proc.wait()
        except OSError as exc:
            stream.write(redact(str(exc)) + "\n")
            status = 127
        event.update(exit_status=status, elapsed_seconds=round(time.monotonic() - started, 3),
                     ended_at=dt.datetime.now(ZoneInfo("Asia/Shanghai")).isoformat())
        stream.write("\n" + json.dumps({"exit_status": status, "elapsed_seconds": event["elapsed_seconds"]}) + "\n")
    with (args.run_dir / "commands.jsonl").open("a") as stream:
        stream.write(redact(json.dumps(event, ensure_ascii=False)) + "\n")
    print(json.dumps({"log": str(log.resolve()), "exit_status": status,
                      "elapsed_seconds": event["elapsed_seconds"]}))
    raise SystemExit(status)


if __name__ == "__main__":
    main()

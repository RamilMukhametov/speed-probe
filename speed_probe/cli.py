"""Command-line interface: arguments, report rendering, exit codes."""

from __future__ import annotations

import argparse
import sys

from .measure import DEFAULT_TIMEOUT_SECONDS, probe
from .stats import Summary

DEFAULT_ATTEMPTS = 10


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the probe."""
    parser = argparse.ArgumentParser(
        prog="speed-probe",
        description="Measure download throughput by fetching a URL sequentially.",
    )
    parser.add_argument("url", help="address to fetch, e.g. a heavy image or file")
    parser.add_argument(
        "-n",
        "--attempts",
        type=int,
        default=DEFAULT_ATTEMPTS,
        help="number of sequential requests (default: %(default)s)",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="per-request timeout in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--family",
        choices=["auto", "ipv4", "ipv6"],
        default="auto",
        help="address family: auto follows system resolution (default: %(default)s)",
    )
    return parser


def render(summary: Summary, url: str, family: str) -> str:
    """Format the probe report for console output."""
    lines = [
        f"Target              : {url}",
        f"Address family      : {family}",
        f"Successful requests : {len(summary.samples)} (failed: {summary.failed})",
        f"Avg response time   : {summary.avg_seconds:.3f} s",
        f"Total downloaded    : {summary.total_bytes / (1024 * 1024):.2f} MiB",
        f"Throughput          : {summary.throughput_mib_per_sec:.2f} MB/s",
    ]
    if summary.failed and summary.last_error:
        lines.append(f"Last error          : {summary.last_error}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Entry point: parse args, run probe, print report, return exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.attempts < 1:
        parser.error("--attempts must be >= 1")
    summary = probe(args.url, args.attempts, args.timeout, args.family)
    print(render(summary, args.url, args.family))
    if not summary.samples:
        print("All requests failed - check the URL and network.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

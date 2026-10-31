"""Command-line entry point for the square dance module importer.

Example:
    python -m sdimport.cli --source ceder --level mainstream --limit 5
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .ceder_client import CederClient
from .importer import run_import
from .sources.ceder import CederSource

# Default vault target: BDP-Obsidian/Square-Modules relative to the workspace root (bdp/).
# square-modules/sd-choreo-importer/sdimport/cli.py -> workspace root is parents[3].
_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_VAULT = _REPO_ROOT / "BDP-Obsidian" / "Square-Modules"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdimport",
        description="Import square dance choreography modules into an Obsidian vault.",
    )
    p.add_argument(
        "--source", default="ceder", choices=["ceder"], help="Import source (default: ceder)."
    )
    p.add_argument(
        "--level",
        default="mainstream",
        help="Dance level (default: mainstream). e.g. mainstream, plus, a1, a2, c1...",
    )
    p.add_argument(
        "--vault",
        type=Path,
        default=DEFAULT_VAULT,
        help=f"Vault folder to write into (default: {DEFAULT_VAULT}).",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to pause between ceder page requests (default: 1.0).",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Stop after this many records are written/skipped (for testing).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and report, but do not write files.",
    )
    return p


def make_source(args: argparse.Namespace):
    if args.source == "ceder":
        client = CederClient(delay=args.delay)
        return CederSource(level=args.level, client=client)
    raise ValueError(f"Unknown source: {args.source}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source = make_source(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    summary = run_import(
        source, args.vault, dry_run=args.dry_run, limit=args.limit
    )
    mode = " (dry run)" if args.dry_run else ""
    print(f"{args.source} / {args.level}{mode}: {summary.as_text()}")
    print(f"vault: {args.vault}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

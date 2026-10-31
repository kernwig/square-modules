"""Command-line entry point for the level classifier.

Two-step, auditable workflow:

  1. Plan (dry run, default) -> writes a TSV report of proposed changes:
         python -m levelclassifier.cli plan --mode mismatch
     Review (and optionally edit/trim rows in) the report.

  2. Apply the approved report:
         python -m levelclassifier.cli apply --report level-report.tsv --apply

``plan`` never modifies the vault. ``apply`` is also dry-run by default and only
writes when ``--apply`` is passed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .planner import apply_report, build_plan, write_report

# Default vault: BDP-Obsidian/Square-Modules relative to the workspace root (bdp/).
# square-modules/level-classifier/levelclassifier/cli.py -> workspace root is parents[3].
_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_VAULT = _REPO_ROOT / "BDP-Obsidian" / "Square-Modules"
DEFAULT_REPORT = Path("level-report.tsv")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="levelclassifier",
        description="Detect and reconcile dance-program level (MS/Plus/A1/A2) of modules.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    common_vault = argparse.ArgumentParser(add_help=False)
    common_vault.add_argument(
        "--vault", type=Path, default=DEFAULT_VAULT,
        help=f"Vault folder to scan (default: {DEFAULT_VAULT}).",
    )

    plan = sub.add_parser(
        "plan", parents=[common_vault],
        help="Classify modules and write a review report (no changes made).",
    )
    plan.add_argument(
        "--mode", choices=["fill", "mismatch", "all"], default="mismatch",
        help="fill: only modules with no level; mismatch: level disagrees with "
             "detection; all: both (default: mismatch).",
    )
    plan.add_argument(
        "--report", type=Path, default=DEFAULT_REPORT,
        help=f"Report file to write (default: {DEFAULT_REPORT}).",
    )

    ap = sub.add_parser(
        "apply", parents=[common_vault],
        help="Apply an approved report: set level + move file.",
    )
    ap.add_argument(
        "--report", type=Path, default=DEFAULT_REPORT,
        help=f"Approved report to apply (default: {DEFAULT_REPORT}).",
    )
    ap.add_argument(
        "--apply", action="store_true",
        help="Actually write changes. Without it, apply runs as a dry run.",
    )
    return p


def _cmd_plan(args: argparse.Namespace) -> int:
    rows = build_plan(args.vault, mode=args.mode)
    write_report(rows, args.vault, args.report)

    by_mode: dict[str, int] = {}
    low_conf = 0
    for r in rows:
        by_mode[r.mode] = by_mode.get(r.mode, 0) + 1
        if r.confidence == "low":
            low_conf += 1
    print(f"planned {len(rows)} change(s) [mode={args.mode}]")
    for m, n in sorted(by_mode.items()):
        print(f"  {m}: {n}")
    if low_conf:
        print(f"  low-confidence rows (review carefully): {low_conf}")
    print(f"report written: {args.report}")
    print("review it, delete any rows you reject, then:")
    print(f"  {sys.executable} -m levelclassifier.cli apply --report {args.report} --apply")
    return 0


def _cmd_apply(args: argparse.Namespace) -> int:
    if not args.report.exists():
        print(f"error: report not found: {args.report}", file=sys.stderr)
        return 2
    res = apply_report(args.report, args.vault, dry_run=not args.apply)
    mode = "" if args.apply else " (dry run)"
    print(f"apply{mode}: changed={res.changed} moved={res.moved} errors={len(res.errors)}")
    for err in res.errors:
        print(f"  ! {err}", file=sys.stderr)
    if not args.apply:
        print("re-run with --apply to write changes.")
    return 0 if not res.errors else 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "plan":
        return _cmd_plan(args)
    if args.command == "apply":
        return _cmd_apply(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

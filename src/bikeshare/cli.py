"""Command line entry point.

bikeshare run                     # extract -> load -> transform -> check -> export
bikeshare run --start 2026-06 --end 2026-08
bikeshare transform               # re-run one step against data already on disk
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

import duckdb

from bikeshare import export, extract, load, quality, report, transform
from bikeshare.config import DEFAULT_END, DEFAULT_START, REPO_ROOT, Paths, default_paths

log = logging.getLogger("bikeshare")

STEPS = ("extract", "load", "transform", "check", "export")


def connect(paths: Paths) -> duckdb.DuckDBPyConnection:
    paths.database.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(paths.database))


def run_step(step: str, args: argparse.Namespace, paths: Paths) -> None:
    started = time.perf_counter()
    log.info("== %s ==", step)
    if step == "extract":
        months = extract.month_range(args.start, args.end)
        extract.extract_trips(paths, months, refresh=args.refresh)
        years = sorted({int(m[:4]) for m in months})
        extract.extract_weather(paths, years, refresh=args.refresh)
    else:
        with connect(paths) as con:
            if step == "load":
                load.load_raw(con, paths)
            elif step == "transform":
                transform.run_models(con)
            elif step == "check":
                quality.run_checks(con)
            elif step == "export":
                export.export_marts(con, paths, args.format)
            elif step == "report":
                report.write_report(con, REPO_ROOT / "docs" / "analysis_results.md")
    log.info("%s finished in %.1fs", step, time.perf_counter() - started)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bikeshare", description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("run", *STEPS, "report"))
    parser.add_argument("--start", default=DEFAULT_START, help="first month, YYYY-MM")
    parser.add_argument("--end", default=DEFAULT_END, help="last month, YYYY-MM")
    parser.add_argument("--refresh", action="store_true", help="re-download files on disk")
    parser.add_argument("--format", choices=("parquet", "csv"), default="parquet")
    parser.add_argument("--skip-extract", action="store_true", help="run: reuse files on disk")
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    paths = default_paths()
    steps = STEPS if args.command == "run" else (args.command,)
    if args.command == "run" and args.skip_extract:
        steps = STEPS[1:]
    try:
        for step in steps:
            run_step(step, args, paths)
    except quality.DataQualityError as exc:
        log.error("%s. Nothing was exported.", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

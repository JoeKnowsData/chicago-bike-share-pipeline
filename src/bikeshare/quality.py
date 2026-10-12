"""Data quality checks.

Each file in sql/checks is a query that returns the rows breaking a rule, so an empty
result means the check passed. A check whose first line is ``-- severity: warn`` only
logs a warning; every other failing check stops the pipeline before anything is exported.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import duckdb

from bikeshare.config import SQL_DIR

log = logging.getLogger(__name__)


@dataclass
class CheckResult:
    name: str
    severity: str
    failing_rows: int

    @property
    def passed(self) -> bool:
        return self.failing_rows == 0


class DataQualityError(RuntimeError):
    pass


def _severity(sql: str) -> str:
    first_line = sql.lstrip().splitlines()[0].lower() if sql.strip() else ""
    return "warn" if first_line.replace(" ", "") == "--severity:warn" else "error"


def run_checks(
    con: duckdb.DuckDBPyConnection, checks_dir: Path = SQL_DIR / "checks"
) -> list[CheckResult]:
    results = []
    for sql_file in sorted(checks_dir.glob("*.sql")):
        sql = sql_file.read_text(encoding="utf-8").strip().rstrip(";")
        failing = con.execute(f"select count(*) from ({sql})").fetchone()[0]
        result = CheckResult(sql_file.stem, _severity(sql), failing)
        if result.passed:
            log.info("check passed: %s", result.name)
        else:
            log.warning("check %s: %s (%s rows)", result.severity, result.name, failing)
        results.append(result)

    errors = [r for r in results if not r.passed and r.severity == "error"]
    if errors:
        names = ", ".join(r.name for r in errors)
        raise DataQualityError(f"{len(errors)} data quality check(s) failed: {names}")
    return results

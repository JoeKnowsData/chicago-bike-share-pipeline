"""Transform: run the SQL models in sql/staging then sql/marts, in file-name order."""

from __future__ import annotations

import logging
import time

import duckdb

from bikeshare.config import SQL_DIR

log = logging.getLogger(__name__)

LAYERS = ("staging", "marts")


def run_models(con: duckdb.DuckDBPyConnection) -> list[str]:
    ran = []
    for layer in LAYERS:
        for sql_file in sorted((SQL_DIR / layer).glob("*.sql")):
            started = time.perf_counter()
            con.execute(sql_file.read_text(encoding="utf-8"))
            log.info("ran %s/%s in %.1fs", layer, sql_file.name, time.perf_counter() - started)
            ran.append(f"{layer}/{sql_file.name}")
    return ran

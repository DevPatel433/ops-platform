from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from .config import settings


@contextmanager
def connect():
    """Open a connection; commits on clean exit, rolls back on error."""
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        yield conn


def init_schema() -> None:
    sql = (Path(__file__).parent / "schema.sql").read_text()
    with connect() as conn:
        conn.execute(sql)

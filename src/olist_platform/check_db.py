"""Verify local PostgreSQL connectivity without changing database objects."""

import os

import psycopg
from dotenv import load_dotenv


def check_connection() -> int:
    """Return PostgreSQL's SELECT 1 result using environment configuration."""
    load_dotenv(override=False)
    with psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=5,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
    if row != (1,):
        raise RuntimeError("Unexpected PostgreSQL connectivity result")
    return row[0]


def main() -> int:
    """Report success or a credential-safe failure and return an exit code."""
    try:
        check_connection()
    except (KeyError, ValueError, psycopg.Error, RuntimeError):
        print("PostgreSQL check failed. Check .env and Docker service status.")
        return 1
    print("PostgreSQL connection OK (SELECT 1).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import sqlite3
from contextlib import closing
from pathlib import Path

import click

DB_PATH = Path("flight_management.db")


def get_connection():
    """Open the database with foreign keys switched on."""
    if not DB_PATH.exists():
        raise click.ClickException(f"Database not found: {DB_PATH.resolve()}")
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    return db


@click.group()
def main():
    """Flight Management Database CLI."""


@main.command()
@click.option("--airport", default="all", help="Filter by airport code, e.g. LHR.")
def flights(airport):
    """Get a list of flight details."""
    query = """
        SELECT flight_number, departure_code, arrival_code,
               departure_time, flight_time_minutes, status
        FROM flight_details
    """
    params = ()
    if airport.lower() != "all":
        query += " WHERE departure_code = ? OR arrival_code = ?"
        params = (airport.upper(), airport.upper())
    query += " ORDER BY departure_time"

    with closing(get_connection()) as db:
        rows = db.execute(query, params).fetchall()

    if not rows:
        click.echo("No flights found.")
        return

    for number, dep, arr, departs, mins, status in rows:
        click.echo(
            f"{number:<7} {dep} -> {arr}  {departs}  {mins // 60}h {mins % 60:02d}m  {status}"
        )


if __name__ == "__main__":
    main()

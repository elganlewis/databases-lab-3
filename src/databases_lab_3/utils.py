"""Database connection handling."""

import math
import sqlite3
from pathlib import Path

import click
from tabulate import tabulate

DB_PATH = Path("flight_management.db")


def get_connection():
    """Open the database with foreign keys switched on."""
    if not DB_PATH.exists():
        raise click.ClickException(f"Database not found: {DB_PATH.resolve()}")
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row  # access columns by name, e.g. row["status"]
    db.execute("PRAGMA foreign_keys = ON")
    return db


def print_table(rows, headers, empty_message="No results found."):
    """Print rows as a table, or a message if there are none."""
    if not rows:
        click.echo(empty_message)
        return
    click.echo(tabulate(rows, headers=headers, tablefmt="simple_outline"))


def format_duration(minutes):
    """Format a number of minutes as e.g. '1h 05m'."""
    return f"{minutes // 60}h {minutes % 60:02d}m"


def available_role(row):
    """Return missing roles (Captain, First Officer) for a flight row."""
    roles = []
    if not row["captain"]:
        roles.append("Captain")
    if not row["first_officer"]:
        roles.append("First Officer")
    return ", ".join(roles) if roles else "-"


def estimate_flight_minutes(lat1, lon1, lat2, lon2, speed_kmh=900):
    """Estimate flight duration in minutes using great-circle distance."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    distance_km = R * 2 * math.asin(math.sqrt(a))
    return round(distance_km / speed_kmh * 60)

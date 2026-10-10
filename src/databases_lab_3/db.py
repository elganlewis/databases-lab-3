"""Database connection handling."""

import sqlite3
from pathlib import Path

import click

DB_PATH = Path("flight_management.db")


def get_connection():
    """Open the database with foreign keys switched on."""
    if not DB_PATH.exists():
        raise click.ClickException(f"Database not found: {DB_PATH.resolve()}")
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row  # access columns by name, e.g. row["status"]
    db.execute("PRAGMA foreign_keys = ON")
    return db

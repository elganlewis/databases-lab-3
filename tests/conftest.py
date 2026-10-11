"""Shared fixtures for all tests.

Uses an in-memory SQLite database so tests are isolated, fast, and never touch
the real flight_management.db file.
"""

import sqlite3
from pathlib import Path

import pytest

SCHEMA_SQL = (
    Path(__file__).parent.parent / "flight_db_create_tables.sql"
).read_text()


@pytest.fixture
def db():
    """Return a fresh in-memory database with the full schema applied."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_SQL)
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Seed helpers – call these inside individual tests as needed
# ---------------------------------------------------------------------------

def seed_airports(db):
    db.execute(
        "INSERT INTO airport (iata_code, icao_code, airport_name, city_name, "
        "country_code, timezone, latitude, longitude, elevation_feet) "
        "VALUES ('LHR', 'EGLL', 'Heathrow', 'London', 'GB', 'Europe/London', "
        "51.477, -0.461, 83)"
    )
    db.execute(
        "INSERT INTO airport (iata_code, icao_code, airport_name, city_name, "
        "country_code, timezone, latitude, longitude, elevation_feet) "
        "VALUES ('JFK', 'KJFK', 'JFK International', 'New York', 'US', "
        "'America/New_York', 40.641, -73.778, 13)"
    )
    db.commit()


def seed_aircraft(db):
    db.execute(
        "INSERT INTO aircraft (registration_number, model, manufacturer, "
        "capacity, range_km, min_runway_m, year_manufactured) "
        "VALUES ('G-TEST', 'A320', 'Airbus', 180, 6300, 1800, 2015)"
    )
    db.commit()


def seed_pilots(db):
    db.execute(
        "INSERT INTO pilot (licence_number, first_name, last_name, hire_date, email) "
        "VALUES ('UK-00001', 'Alice', 'Smith', '2020-01-01', 'alice@test.com')"
    )
    db.execute(
        "INSERT INTO pilot (licence_number, first_name, last_name) "
        "VALUES ('UK-00002', 'Bob', 'Jones')"
    )
    db.commit()


def seed_flight(db):
    """Seed airports, aircraft, pilots and one flight. Returns flight_id."""
    seed_airports(db)
    seed_aircraft(db)
    seed_pilots(db)
    cursor = db.execute(
        "INSERT INTO flight (flight_number, departure_airport_id, arrival_airport_id, "
        "aircraft_id, departure_time, flight_time_minutes) "
        "VALUES ('TS001', 1, 2, 1, '2030-06-01 09:00:00', 480)"
    )
    db.commit()
    return cursor.lastrowid

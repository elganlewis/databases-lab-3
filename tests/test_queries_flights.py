"""Tests for flight and flight-crew queries."""

import sqlite3

import pytest

from databases_lab_3.queries.flights import (
    add_flight,
    assign_pilot_to_flight,
    cancel_flight,
    check_pilot_conflict,
    check_role_taken,
    delay_flight,
    get_available_flights,
    get_available_pilots,
    get_flight_by_id,
    get_flight_crew,
    get_flight_details,
    get_flights,
    unassign_pilot_from_flight,
    update_flight,
)

from .conftest import seed_aircraft, seed_airports, seed_flight

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add_flight(
    db,
    number="TS001",
    dep_id=1,
    arr_id=2,
    aircraft_id=1,
    departure="2030-06-01 09:00:00",
    duration=480,
):
    return add_flight(db, number, dep_id, arr_id, aircraft_id, departure, duration)


# ---------------------------------------------------------------------------
# get_flights
# ---------------------------------------------------------------------------


class TestGetFlights:
    def test_empty(self, db):
        assert get_flights(db) == []

    def test_returns_all(self, db):
        seed_flight(db)
        assert len(get_flights(db)) == 1

    def test_filter_departure_airport(self, db):
        seed_flight(db)
        assert len(get_flights(db, departure_airport="LHR")) == 1
        assert len(get_flights(db, departure_airport="JFK")) == 0

    def test_filter_arrival_airport(self, db):
        seed_flight(db)
        assert len(get_flights(db, arrival_airport="JFK")) == 1

    def test_filter_status(self, db):
        seed_flight(db)
        assert len(get_flights(db, status=("Scheduled",))) == 1
        assert len(get_flights(db, status=("Cancelled",))) == 0

    def test_exclude_status(self, db):
        seed_flight(db)
        assert len(get_flights(db, exclude_status=("Scheduled",))) == 0

    def test_filter_date(self, db):
        seed_flight(db)
        assert len(get_flights(db, date="2030-06-01")) == 1
        assert len(get_flights(db, date="2030-06-02")) == 0


# ---------------------------------------------------------------------------
# add_flight / get_flight_by_id
# ---------------------------------------------------------------------------


class TestAddAndGetFlight:
    def test_add_returns_id(self, db):
        seed_airports(db)
        seed_aircraft(db)
        flight_id = _add_flight(db)
        assert isinstance(flight_id, int) and flight_id > 0

    def test_get_by_id(self, db):
        flight_id = seed_flight(db)
        row = get_flight_by_id(db, flight_id)
        assert row is not None
        assert row["flight_number"] == "TS001"

    def test_get_missing_returns_none(self, db):
        assert get_flight_by_id(db, 9999) is None

    def test_defaults_to_scheduled(self, db):
        seed_airports(db)
        seed_aircraft(db)
        flight_id = _add_flight(db)
        assert get_flight_by_id(db, flight_id)["status"] == "Scheduled"

    def test_same_departure_arrival_raises(self, db):
        seed_airports(db)
        seed_aircraft(db)
        with pytest.raises(sqlite3.IntegrityError):
            add_flight(db, "BAD", 1, 1, 1, "2030-06-01 09:00:00", 60)


# ---------------------------------------------------------------------------
# update_flight
# ---------------------------------------------------------------------------


class TestUpdateFlight:
    def test_update_flight_number(self, db):
        flight_id = seed_flight(db)
        update_flight(db, flight_id, flight_number="TS999")
        assert get_flight_by_id(db, flight_id)["flight_number"] == "TS999"

    def test_update_duration(self, db):
        flight_id = seed_flight(db)
        update_flight(db, flight_id, flight_time_minutes=500)
        assert get_flight_by_id(db, flight_id)["flight_time_minutes"] == 500

    def test_no_fields_returns_zero(self, db):
        flight_id = seed_flight(db)
        assert update_flight(db, flight_id) == 0


# ---------------------------------------------------------------------------
# delay_flight / cancel_flight
# ---------------------------------------------------------------------------


class TestDelayFlight:
    def test_delays_scheduled_flight(self, db):
        flight_id = seed_flight(db)
        assert delay_flight(db, flight_id, 90) == 1
        assert get_flight_by_id(db, flight_id)["status"] == "Delayed"

    def test_shifts_departure_time(self, db):
        flight_id = seed_flight(db)
        delay_flight(db, flight_id, 60)
        row = get_flight_by_id(db, flight_id)
        assert "10:00" in row["departure_time"]

    def test_does_not_delay_cancelled(self, db):
        flight_id = seed_flight(db)
        cancel_flight(db, flight_id)
        assert delay_flight(db, flight_id, 30) == 0

    def test_missing_flight_returns_zero(self, db):
        assert delay_flight(db, 9999, 30) == 0


class TestCancelFlight:
    def test_cancels_scheduled(self, db):
        flight_id = seed_flight(db)
        assert cancel_flight(db, flight_id) == 1
        assert get_flight_by_id(db, flight_id)["status"] == "Cancelled"

    def test_cancels_delayed(self, db):
        flight_id = seed_flight(db)
        delay_flight(db, flight_id, 30)
        assert cancel_flight(db, flight_id) == 1

    def test_missing_flight_returns_zero(self, db):
        assert cancel_flight(db, 9999) == 0


# ---------------------------------------------------------------------------
# get_available_flights
# ---------------------------------------------------------------------------


class TestGetAvailableFlights:
    def test_unassigned_flight_appears(self, db):
        seed_flight(db)
        rows = get_available_flights(db)
        assert len(rows) == 1

    def test_fully_crewed_flight_excluded(self, db):
        flight_id = seed_flight(db)
        pilot_ids = db.execute("SELECT pilot_id FROM pilot").fetchall()
        assign_pilot_to_flight(db, flight_id, pilot_ids[0]["pilot_id"], "Captain")
        assign_pilot_to_flight(db, flight_id, pilot_ids[1]["pilot_id"], "First Officer")
        assert get_available_flights(db) == []


# ---------------------------------------------------------------------------
# get_flight_details
# ---------------------------------------------------------------------------


class TestGetFlightDetails:
    def test_returns_flight_and_crew(self, db):
        flight_id = seed_flight(db)
        flight, crew = get_flight_details(db, flight_id)
        assert flight is not None
        assert crew == []

    def test_missing_flight_returns_none(self, db):
        flight, crew = get_flight_details(db, 9999)
        assert flight is None


# ---------------------------------------------------------------------------
# Crew assignment
# ---------------------------------------------------------------------------


class TestCrewAssignment:
    def test_assign_and_retrieve(self, db):
        flight_id = seed_flight(db)
        pilot_id = db.execute("SELECT pilot_id FROM pilot LIMIT 1").fetchone()[
            "pilot_id"
        ]
        assign_pilot_to_flight(db, flight_id, pilot_id, "Captain")
        crew = get_flight_crew(db, flight_id)
        assert len(crew) == 1
        assert crew[0]["role"] == "Captain"

    def test_check_role_taken_true(self, db):
        flight_id = seed_flight(db)
        pilot_id = db.execute("SELECT pilot_id FROM pilot LIMIT 1").fetchone()[
            "pilot_id"
        ]
        assign_pilot_to_flight(db, flight_id, pilot_id, "Captain")
        assert check_role_taken(db, flight_id, "Captain") == 1

    def test_check_role_taken_false(self, db):
        flight_id = seed_flight(db)
        assert check_role_taken(db, flight_id, "Captain") == 0

    def test_unassign_pilot(self, db):
        flight_id = seed_flight(db)
        pilot_id = db.execute("SELECT pilot_id FROM pilot LIMIT 1").fetchone()[
            "pilot_id"
        ]
        assign_pilot_to_flight(db, flight_id, pilot_id, "Captain")
        assert unassign_pilot_from_flight(db, flight_id, pilot_id) == 1
        assert get_flight_crew(db, flight_id) == []

    def test_unassign_missing_returns_zero(self, db):
        flight_id = seed_flight(db)
        assert unassign_pilot_from_flight(db, flight_id, 9999) == 0

    def test_check_no_conflict(self, db):
        flight_id = seed_flight(db)
        pilot_id = db.execute("SELECT pilot_id FROM pilot LIMIT 1").fetchone()[
            "pilot_id"
        ]
        assert check_pilot_conflict(db, pilot_id, flight_id) == []

    def test_check_conflict_detected(self, db):
        """Assign pilot to flight 1, then check for conflict on an overlapping flight 2."""
        flight_id_1 = seed_flight(db)
        flight_id_2 = add_flight(db, "TS002", 1, 2, 1, "2030-06-01 11:00:00", 480)
        pilot_id = db.execute("SELECT pilot_id FROM pilot LIMIT 1").fetchone()[
            "pilot_id"
        ]
        assign_pilot_to_flight(db, flight_id_1, pilot_id, "Captain")
        conflicts = check_pilot_conflict(db, pilot_id, flight_id_2)
        assert len(conflicts) == 1

    def test_no_conflict_non_overlapping(self, db):
        """Pilot on flight 1 (morning) should have no conflict for flight 2 (next day)."""
        flight_id_1 = seed_flight(db)
        flight_id_2 = add_flight(db, "TS002", 1, 2, 1, "2030-06-02 09:00:00", 480)
        pilot_id = db.execute("SELECT pilot_id FROM pilot LIMIT 1").fetchone()[
            "pilot_id"
        ]
        assign_pilot_to_flight(db, flight_id_1, pilot_id, "Captain")
        assert check_pilot_conflict(db, pilot_id, flight_id_2) == []


# ---------------------------------------------------------------------------
# get_available_pilots
# ---------------------------------------------------------------------------


class TestGetAvailablePilots:
    def test_all_pilots_free(self, db):
        flight_id = seed_flight(db)
        rows = get_available_pilots(db, flight_id)
        assert len(rows) == 2

    def test_assigned_pilot_excluded(self, db):
        flight_id = seed_flight(db)
        pilot_id = db.execute("SELECT pilot_id FROM pilot LIMIT 1").fetchone()[
            "pilot_id"
        ]
        assign_pilot_to_flight(db, flight_id, pilot_id, "Captain")
        # Add a second overlapping flight
        flight_id_2 = add_flight(db, "TS002", 1, 2, 1, "2030-06-01 11:00:00", 480)
        rows = get_available_pilots(db, flight_id_2)
        licences = [r["licence_number"] for r in rows]
        captain = db.execute(
            "SELECT licence_number FROM pilot WHERE pilot_id = ?", (pilot_id,)
        ).fetchone()["licence_number"]
        assert captain not in licences

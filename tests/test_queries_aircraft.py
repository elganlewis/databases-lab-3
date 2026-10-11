"""Tests for aircraft queries."""

import sqlite3

import pytest

from databases_lab_3.queries.aircraft import (
    add_aircraft,
    delete_aircraft,
    get_aircraft,
    get_aircraft_by_registration,
    update_aircraft,
)


def _add(db, registration="G-TEST", model="A320", manufacturer="Airbus",
         capacity=180, range_km=6300, min_runway_m=1800, year=2015):
    return add_aircraft(db, registration, model, manufacturer,
                        capacity, range_km, min_runway_m, year)


class TestGetAircraft:
    def test_empty_returns_nothing(self, db):
        assert get_aircraft(db) == []

    def test_returns_all(self, db):
        _add(db, "G-AAA")
        _add(db, "G-BBB")
        rows = get_aircraft(db)
        assert len(rows) == 2

    def test_filter_by_registration(self, db):
        _add(db, "G-AAA")
        _add(db, "G-BBB")
        rows = get_aircraft(db, registration="G-AAA")
        assert len(rows) == 1
        assert rows[0]["registration_number"] == "G-AAA"

    def test_filter_by_status(self, db):
        _add(db, "G-AAA")
        aircraft_id = get_aircraft(db, registration="G-AAA")[0]["aircraft_id"]
        update_aircraft(db, aircraft_id, status="Retired")
        assert len(get_aircraft(db, status="Active")) == 0
        assert len(get_aircraft(db, status="Retired")) == 1

    def test_ordered_by_registration(self, db):
        _add(db, "G-ZZZ")
        _add(db, "G-AAA")
        rows = get_aircraft(db)
        assert rows[0]["registration_number"] == "G-AAA"


class TestGetAircraftByRegistration:
    def test_returns_row(self, db):
        _add(db, "G-TEST")
        row = get_aircraft_by_registration(db, "G-TEST")
        assert row is not None
        assert row["registration_number"] == "G-TEST"

    def test_case_insensitive(self, db):
        _add(db, "G-TEST")
        assert get_aircraft_by_registration(db, "g-test") is not None

    def test_missing_returns_none(self, db):
        assert get_aircraft_by_registration(db, "G-NONE") is None


class TestAddAircraft:
    def test_returns_id(self, db):
        aircraft_id = _add(db)
        assert isinstance(aircraft_id, int)
        assert aircraft_id > 0

    def test_defaults_to_active(self, db):
        _add(db)
        row = get_aircraft(db)[0]
        assert row["status"] == "Active"

    def test_duplicate_registration_raises(self, db):
        _add(db, "G-DUPE")
        with pytest.raises(sqlite3.IntegrityError):
            _add(db, "G-DUPE")


class TestUpdateAircraft:
    def test_update_model(self, db):
        aircraft_id = _add(db)
        update_aircraft(db, aircraft_id, model="A321")
        assert get_aircraft(db)[0]["model"] == "A321"

    def test_update_status(self, db):
        aircraft_id = _add(db)
        update_aircraft(db, aircraft_id, status="In Maintenance")
        assert get_aircraft(db)[0]["status"] == "In Maintenance"

    def test_no_fields_returns_zero(self, db):
        aircraft_id = _add(db)
        assert update_aircraft(db, aircraft_id) == 0

    def test_returns_rowcount(self, db):
        aircraft_id = _add(db)
        assert update_aircraft(db, aircraft_id, model="B737") == 1


class TestDeleteAircraft:
    def test_deletes_successfully(self, db):
        aircraft_id = _add(db)
        assert delete_aircraft(db, aircraft_id) == 1
        assert get_aircraft(db) == []

    def test_missing_returns_zero(self, db):
        assert delete_aircraft(db, 9999) == 0

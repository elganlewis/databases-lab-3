"""Tests for airport and runway queries."""

import sqlite3

import pytest

from databases_lab_3.queries.airports import (
    add_airport,
    add_runway,
    delete_airport,
    get_airport_by_code,
    get_airports,
    get_runway,
    update_airport,
    update_runway,
)


def _add_airport(
    db,
    iata="LHR",
    icao="EGLL",
    name="Heathrow",
    city="London",
    country="GB",
    tz="Europe/London",
    lat=51.477,
    lon=-0.461,
    elev=83,
):
    return add_airport(db, iata, icao, name, city, country, tz, lat, lon, elev)


class TestGetAirports:
    def test_empty_returns_nothing(self, db):
        assert get_airports(db) == []

    def test_returns_all(self, db):
        _add_airport(db, iata="LHR", icao="EGLL")
        _add_airport(
            db,
            iata="JFK",
            icao="KJFK",
            city="New York",
            country="US",
            tz="America/New_York",
            lat=40.6,
            lon=-73.8,
            elev=13,
        )
        assert len(get_airports(db)) == 2

    def test_filter_by_iata(self, db):
        _add_airport(db, iata="LHR", icao="EGLL")
        _add_airport(
            db,
            iata="JFK",
            icao="KJFK",
            city="New York",
            country="US",
            tz="America/New_York",
            lat=40.6,
            lon=-73.8,
            elev=13,
        )
        rows = get_airports(db, code="LHR")
        assert len(rows) == 1
        assert rows[0]["iata_code"] == "LHR"

    def test_filter_by_icao(self, db):
        _add_airport(db, iata="LHR", icao="EGLL")
        rows = get_airports(db, code="EGLL")
        assert len(rows) == 1

    def test_filter_by_country(self, db):
        _add_airport(db, iata="LHR", icao="EGLL")
        _add_airport(
            db,
            iata="JFK",
            icao="KJFK",
            city="New York",
            country="US",
            tz="America/New_York",
            lat=40.6,
            lon=-73.8,
            elev=13,
        )
        rows = get_airports(db, country="GB")
        assert len(rows) == 1
        assert rows[0]["country_code"] == "GB"


class TestGetAirportByCode:
    def test_finds_by_iata(self, db):
        _add_airport(db)
        assert get_airport_by_code(db, "LHR") is not None

    def test_finds_by_icao(self, db):
        _add_airport(db)
        assert get_airport_by_code(db, "EGLL") is not None

    def test_case_insensitive(self, db):
        _add_airport(db)
        assert get_airport_by_code(db, "lhr") is not None

    def test_missing_returns_none(self, db):
        assert get_airport_by_code(db, "XXX") is None


class TestAddAirport:
    def test_returns_id(self, db):
        airport_id = _add_airport(db)
        assert isinstance(airport_id, int) and airport_id > 0

    def test_duplicate_icao_raises(self, db):
        _add_airport(db, iata="LHR", icao="EGLL")
        with pytest.raises(sqlite3.IntegrityError):
            _add_airport(db, iata="LGW", icao="EGLL")

    def test_null_iata_allowed(self, db):
        airport_id = add_airport(
            db, None, "ZZZZ", "No IATA Airport", "Nowhere", "GB", "UTC", 0.0, 0.0, 0
        )
        assert airport_id > 0


class TestUpdateAirport:
    def test_update_name(self, db):
        airport_id = _add_airport(db)
        update_airport(db, airport_id, airport_name="London Heathrow")
        row = get_airports(db, code="LHR")[0]
        assert row["airport_name"] == "London Heathrow"

    def test_no_fields_returns_zero(self, db):
        airport_id = _add_airport(db)
        assert update_airport(db, airport_id) == 0


class TestDeleteAirport:
    def test_deletes_unused_airport(self, db):
        airport_id = _add_airport(db)
        assert delete_airport(db, airport_id) == 1
        assert get_airports(db) == []

    def test_missing_returns_zero(self, db):
        assert delete_airport(db, 9999) == 0


class TestRunways:
    def test_add_and_retrieve(self, db):
        airport_id = _add_airport(db)
        add_runway(db, airport_id, "09L", 3902, "Asphalt")
        row = get_runway(db, airport_id, "09L")
        assert row is not None
        assert row["length_m"] == 3902
        assert row["surface"] == "Asphalt"

    def test_get_missing_runway_returns_none(self, db):
        airport_id = _add_airport(db)
        assert get_runway(db, airport_id, "99X") is None

    def test_duplicate_runway_raises(self, db):
        airport_id = _add_airport(db)
        add_runway(db, airport_id, "09L", 3902, "Asphalt")
        with pytest.raises(sqlite3.IntegrityError):
            add_runway(db, airport_id, "09L", 3000, "Concrete")

    def test_update_runway_length(self, db):
        airport_id = _add_airport(db)
        add_runway(db, airport_id, "09L", 3902, "Asphalt")
        update_runway(db, airport_id, "09L", length_m=4000)
        assert get_runway(db, airport_id, "09L")["length_m"] == 4000

    def test_update_runway_surface(self, db):
        airport_id = _add_airport(db)
        add_runway(db, airport_id, "09L", 3902, "Asphalt")
        update_runway(db, airport_id, "09L", surface="Concrete")
        assert get_runway(db, airport_id, "09L")["surface"] == "Concrete"

    def test_update_no_fields_returns_zero(self, db):
        airport_id = _add_airport(db)
        add_runway(db, airport_id, "09L", 3902, "Asphalt")
        assert update_runway(db, airport_id, "09L") == 0

    def test_runway_deleted_with_airport(self, db):
        airport_id = _add_airport(db)
        add_runway(db, airport_id, "09L", 3902, "Asphalt")
        delete_airport(db, airport_id)
        assert get_runway(db, airport_id, "09L") is None

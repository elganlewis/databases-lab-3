"""Tests for pilot queries."""

import sqlite3

import pytest

from databases_lab_3.queries.pilots import (
    add_pilot,
    add_pilot_phone,
    delete_pilot,
    delete_pilot_phone,
    get_pilot_by_licence,
    get_pilots,
    update_pilot,
)


def _add(db, licence="UK-00001", first="Alice", last="Smith",
         hire_date="2020-01-01", email="alice@test.com"):
    return add_pilot(db, licence, first, last, hire_date, email)


class TestGetPilots:
    def test_empty_returns_nothing(self, db):
        assert get_pilots(db, None, None) == []

    def test_returns_all(self, db):
        _add(db, "UK-00001")
        _add(db, "UK-00002", first="Bob", last="Jones", email="bob@test.com")
        assert len(get_pilots(db, None, None)) == 2

    def test_filter_by_licence(self, db):
        _add(db, "UK-00001")
        _add(db, "UK-00002", first="Bob", last="Jones", email="bob@test.com")
        rows = get_pilots(db, licence="UK-00001", name=None)
        assert len(rows) == 1
        assert rows[0]["licence_number"] == "UK-00001"

    def test_filter_by_full_name(self, db):
        _add(db, "UK-00001", first="Alice", last="Smith")
        rows = get_pilots(db, licence=None, name="Alice Smith")
        assert len(rows) == 1

    def test_filter_by_last_name(self, db):
        _add(db, "UK-00001", first="Alice", last="Smith")
        rows = get_pilots(db, licence=None, name="Smith")
        assert len(rows) == 1

    def test_filter_by_first_name(self, db):
        _add(db, "UK-00001", first="Alice", last="Smith")
        rows = get_pilots(db, licence=None, name="Alice")
        assert len(rows) == 1

    def test_phone_numbers_concatenated(self, db):
        pilot_id = _add(db)
        add_pilot_phone(db, pilot_id, "+44 7700 000001")
        add_pilot_phone(db, pilot_id, "+44 7700 000002")
        row = get_pilots(db, None, None)[0]
        assert "+44 7700 000001" in row["phone_numbers"]
        assert "+44 7700 000002" in row["phone_numbers"]

    def test_no_phone_returns_none(self, db):
        _add(db)
        row = get_pilots(db, None, None)[0]
        assert row["phone_numbers"] is None


class TestGetPilotByLicence:
    def test_returns_row(self, db):
        _add(db, "UK-00001")
        row = get_pilot_by_licence(db, "UK-00001")
        assert row is not None
        assert row["first_name"] == "Alice"

    def test_missing_returns_none(self, db):
        assert get_pilot_by_licence(db, "UK-NONE") is None


class TestAddPilot:
    def test_returns_id(self, db):
        pilot_id = _add(db)
        assert isinstance(pilot_id, int) and pilot_id > 0

    def test_optional_fields_nullable(self, db):
        pilot_id = add_pilot(db, "UK-99999", "No", "Details", None, None)
        row = get_pilots(db, "UK-99999", None)[0]
        assert row["hire_date"] is None
        assert row["email"] is None

    def test_duplicate_licence_raises(self, db):
        _add(db, "UK-00001")
        with pytest.raises(sqlite3.IntegrityError):
            _add(db, "UK-00001", first="Other", email="other@test.com")

    def test_duplicate_email_raises(self, db):
        _add(db, "UK-00001", email="shared@test.com")
        with pytest.raises(sqlite3.IntegrityError):
            _add(db, "UK-00002", email="shared@test.com")


class TestUpdatePilot:
    def test_update_name(self, db):
        pilot_id = _add(db)
        update_pilot(db, pilot_id, first_name="Alicia")
        row = get_pilots(db, None, None)[0]
        assert row["first_name"] == "Alicia"

    def test_update_email(self, db):
        pilot_id = _add(db)
        update_pilot(db, pilot_id, email="new@test.com")
        assert get_pilots(db, None, None)[0]["email"] == "new@test.com"

    def test_no_fields_returns_zero(self, db):
        pilot_id = _add(db)
        assert update_pilot(db, pilot_id) == 0

    def test_returns_rowcount(self, db):
        pilot_id = _add(db)
        assert update_pilot(db, pilot_id, last_name="Brown") == 1


class TestDeletePilot:
    def test_deletes_successfully(self, db):
        pilot_id = _add(db)
        assert delete_pilot(db, pilot_id) == 1
        assert get_pilots(db, None, None) == []

    def test_missing_returns_zero(self, db):
        assert delete_pilot(db, 9999) == 0

    def test_phone_numbers_cascade(self, db):
        pilot_id = _add(db)
        add_pilot_phone(db, pilot_id, "+44 7700 000001")
        delete_pilot(db, pilot_id)
        # Phone row should be gone (CASCADE)
        row = db.execute(
            "SELECT * FROM pilot_phone WHERE pilot_id = ?", (pilot_id,)
        ).fetchone()
        assert row is None


class TestPilotPhone:
    def test_add_phone(self, db):
        pilot_id = _add(db)
        add_pilot_phone(db, pilot_id, "+44 7700 000001")
        row = get_pilots(db, None, None)[0]
        assert "+44 7700 000001" in row["phone_numbers"]

    def test_duplicate_phone_raises(self, db):
        pilot_id = _add(db)
        add_pilot_phone(db, pilot_id, "+44 7700 000001")
        with pytest.raises(sqlite3.IntegrityError):
            add_pilot_phone(db, pilot_id, "+44 7700 000001")

    def test_delete_phone(self, db):
        pilot_id = _add(db)
        add_pilot_phone(db, pilot_id, "+44 7700 000001")
        assert delete_pilot_phone(db, pilot_id, "+44 7700 000001") == 1
        assert get_pilots(db, None, None)[0]["phone_numbers"] is None

    def test_delete_missing_phone_returns_zero(self, db):
        pilot_id = _add(db)
        assert delete_pilot_phone(db, pilot_id, "+00 0000 000000") == 0

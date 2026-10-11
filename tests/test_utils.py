"""Tests for pure-Python utility functions."""


from databases_lab_3.utils import (
    available_role,
    estimate_flight_minutes,
    format_duration,
)


class TestFormatDuration:
    def test_whole_hours(self):
        assert format_duration(120) == "2h 00m"

    def test_hours_and_minutes(self):
        assert format_duration(95) == "1h 35m"

    def test_less_than_one_hour(self):
        assert format_duration(45) == "0h 45m"

    def test_single_digit_minutes_padded(self):
        assert format_duration(61) == "1h 01m"


class TestEstimateFlightMinutes:
    def test_same_location_is_zero(self):
        assert estimate_flight_minutes(51.5, -0.5, 51.5, -0.5) == 0

    def test_lhr_to_jfk_roughly_six_to_eight_hours(self):
        # LHR: 51.477, -0.461 / JFK: 40.641, -73.778
        # Great-circle at 900 km/h ≈ 369 min; real flights are longer due to routing
        minutes = estimate_flight_minutes(51.477, -0.461, 40.641, -73.778)
        assert 340 <= minutes <= 480

    def test_short_hop_less_than_long_haul(self):
        short = estimate_flight_minutes(51.5, -0.5, 48.9, 2.35)  # LHR -> CDG
        long_ = estimate_flight_minutes(51.5, -0.5, 40.6, -73.8)  # LHR -> JFK
        assert short < long_

    def test_symmetric(self):
        a_to_b = estimate_flight_minutes(51.5, -0.5, 40.6, -73.8)
        b_to_a = estimate_flight_minutes(40.6, -73.8, 51.5, -0.5)
        assert a_to_b == b_to_a


class TestAvailableRole:
    def test_both_missing(self):
        row = {"captain": None, "first_officer": None}
        assert available_role(row) == "Captain, First Officer"

    def test_captain_missing(self):
        row = {"captain": None, "first_officer": "Bob"}
        assert available_role(row) == "Captain"

    def test_first_officer_missing(self):
        row = {"captain": "Alice", "first_officer": None}
        assert available_role(row) == "First Officer"

    def test_fully_crewed(self):
        row = {"captain": "Alice", "first_officer": "Bob"}
        assert available_role(row) == "-"

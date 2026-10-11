"""SQL queries. Each function takes an open connection and returns rows."""

from databases_lab_3.queries.aircraft import (
    add_aircraft,
    delete_aircraft,
    get_aircraft,
    get_aircraft_by_registration,
    update_aircraft,
)
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
    refresh_flight_statuses,
    unassign_pilot_from_flight,
    update_flight,
)
from databases_lab_3.queries.pilots import (
    add_pilot,
    add_pilot_phone,
    delete_pilot,
    delete_pilot_phone,
    get_pilot_by_licence,
    get_pilot_schedule,
    get_pilots,
    update_pilot,
)

__all__ = [
    # aircraft
    "add_aircraft",
    "delete_aircraft",
    "get_aircraft",
    "get_aircraft_by_registration",
    "update_aircraft",
    # airports
    "add_airport",
    "add_runway",
    "delete_airport",
    "get_airport_by_code",
    "get_airports",
    "get_runway",
    "update_airport",
    "update_runway",
    # flights
    "add_flight",
    "assign_pilot_to_flight",
    "cancel_flight",
    "check_pilot_conflict",
    "check_role_taken",
    "delay_flight",
    "get_available_flights",
    "get_available_pilots",
    "get_flight_by_id",
    "get_flight_crew",
    "get_flight_details",
    "get_flights",
    "refresh_flight_statuses",
    "unassign_pilot_from_flight",
    "update_flight",
    # pilots
    "add_pilot",
    "add_pilot_phone",
    "delete_pilot",
    "delete_pilot_phone",
    "get_pilot_by_licence",
    "get_pilot_schedule",
    "get_pilots",
    "update_pilot",
]

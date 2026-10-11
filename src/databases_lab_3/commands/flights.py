from contextlib import closing

import click

import databases_lab_3.queries as queries
from databases_lab_3.utils import (
    available_role,
    format_duration,
    get_connection,
    print_table,
)


@click.group()
def flights():
    """Flight commands."""


@flights.command("list")
@click.option(
    "--departure-airport",
    "-D",
    default=None,
    help="Filter by departure airport code, e.g. LHR.",
)
@click.option(
    "--arrival-airport",
    "-A",
    default=None,
    help="Filter by arrival airport code, e.g. JFK.",
)
@click.option(
    "--status",
    "-s",
    multiple=True,
    help="Only show flights with this status. Repeatable, e.g. -s scheduled -s delayed",
)
@click.option(
    "--exclude-status",
    "-x",
    multiple=True,
    help="Hide flights with this status. Repeatable, e.g. -x completed -x cancelled.",
)
@click.option(
    "--date",
    "-d",
    default=None,
    help="Filter by departure day in yyyy-mm-dd format, e.g. 2026-10-19.",
)
def flight_list(departure_airport, arrival_airport, status, exclude_status, date):
    """Get a list of flight details."""
    with closing(get_connection()) as db:
        rows = queries.get_flights(
            db,
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            status=status,
            exclude_status=exclude_status,
            date=date,
        )

    table = [
        [
            row["flight_id"],
            row["flight_number"],
            f"{row['departure_code']} -> {row['arrival_code']}",
            row["departure_time"],
            format_duration(row["flight_time_minutes"]),
            row["status"],
        ]
        for row in rows
    ]
    print_table(
        table,
        headers=[
            "Flight ID",
            "Flight Number",
            "Departure -> Arrival",
            "Departure Time",
            "Flight Length",
            "Status",
        ],
        empty_message="No flights found.",
    )


@flights.command("needs-crew")
def needs_crew():
    """List flights with unfilled Captain or First Officer roles."""
    with closing(get_connection()) as db:
        rows = queries.get_available_flights(db)

    table = [
        [
            row["flight_id"],
            row["flight_number"],
            f"{row['departure_code']} -> {row['arrival_code']}",
            row["departure_time"],
            row["arrival_time"],
            available_role(row),
            row["status"],
        ]
        for row in rows
    ]
    print_table(
        table,
        headers=[
            "Flight ID",
            "Flight Number",
            "Departure -> Arrival",
            "Departure Time",
            "Arrival Time",
            "Missing Role",
            "Status",
        ],
        empty_message="No flights found.",
    )


@flights.command("crew")
@click.argument("flight_id", type=int)
def crew(flight_id):
    """List pilots assigned to a flight.

    FLIGHT_ID is the numeric flight ID (see 'flights needs-crew').
    """
    with closing(get_connection()) as db:
        rows = queries.get_flight_crew(db, flight_id)

    table = [
        [row["licence_number"], f"{row['first_name']} {row['last_name']}", row["role"]]
        for row in rows
    ]
    print_table(
        table,
        headers=["Licence Number", "Name", "Role"],
        empty_message=f"No crew assigned to flight {flight_id}.",
    )


@flights.command("available-pilots")
@click.argument("flight_id", type=int)
def available_pilots(flight_id):
    """List pilots available for a given flight (no scheduling conflicts).

    FLIGHT_ID is the numeric flight ID (see 'flights needs-crew').
    """
    with closing(get_connection()) as db:
        rows = queries.get_available_pilots(db, flight_id)

    table = [
        [row["licence_number"], f"{row['first_name']} {row['last_name']}"]
        for row in rows
    ]
    print_table(
        table,
        headers=["Licence Number", "Name"],
        empty_message=f"No pilots available for flight {flight_id}.",
    )


@flights.command("assign")
@click.option("--flight-id", "-f", type=int, prompt="Flight ID")
@click.option("--licence-number", "-l", prompt="Licence number")
@click.option(
    "--role",
    "-r",
    type=click.Choice(["Captain", "First Officer"], case_sensitive=False),
    prompt="Role",
    help="Role to assign: Captain or 'First Officer'.",
)
def assign_pilot(flight_id, licence_number, role):
    """Assign a pilot to a flight."""
    role = "First Officer" if role.lower() == "first officer" else "Captain"

    with closing(get_connection()) as db:
        pilot = queries.get_pilot_by_licence(db, licence_number)
        if pilot is None:
            raise click.ClickException(
                f"No pilot found with licence number {licence_number!r}."
            )

        conflicts = queries.check_pilot_conflict(db, pilot["pilot_id"], flight_id)
        if conflicts:
            lines = "\n".join(
                f"  {r['flight_number']}  {r['departure_time']} – {r['arrival_time']}"
                for r in conflicts
            )
            raise click.ClickException(
                f"Pilot {licence_number} has a scheduling conflict:\n{lines}"
            )

        if queries.check_role_taken(db, flight_id, role):
            raise click.ClickException(
                f"Flight {flight_id} already has a {role} assigned."
            )

        queries.assign_pilot_to_flight(db, flight_id, pilot["pilot_id"], role)

    name = f"{pilot['first_name']} {pilot['last_name']}"
    click.echo(f"Assigned {name} ({licence_number}) as {role} on flight {flight_id}.")


@flights.command("delay")
def delay_flight():
    pass  # TODO: add delay


@flights.command("add")
def add_flight():
    pass  # TODO: add add command


@flights.command("update")
@click.option("--flight-id", "-f", prompt="FlightID")
def update_flight(flight_id):
    pass  # TODO: add update command

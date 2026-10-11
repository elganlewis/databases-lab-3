from contextlib import closing

import click

import databases_lab_3.queries as queries
from databases_lab_3.utils import (
    available_role,
    estimate_flight_minutes,
    format_duration,
    get_connection,
    print_table,
)


@click.group()
def flights():
    """Commands for managing flights and crew assignments."""


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
    help=(
        "Only show flights with this status. Repeatable, e.g. -s scheduled -s delayed."
    ),
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
    help="Filter by departure day in YYYY-MM-DD format, e.g. 2026-10-19.",
)
def flight_list(departure_airport, arrival_airport, status, exclude_status, date):
    """List flights with their ID, route, departure time, duration and status.

    Combine filters freely, e.g. --departure-airport LHR --status scheduled.
    Use the Flight ID shown here with other commands such as 'flights details'.
    """
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
    """List scheduled or delayed flights missing a Captain or First Officer."""
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
    """List the pilots assigned to a flight.

    FLIGHT_ID is the numeric flight ID (see: flights list).
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
    """List pilots with no scheduling conflict for a flight.

    FLIGHT_ID is the numeric flight ID (see: flights list).
    A pilot is excluded if they are already on any flight whose time window
    overlaps with this one.
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


@flights.command("assign-pilot")
@click.option(
    "--flight-id",
    "-f",
    type=int,
    prompt="Flight ID",
    help="Numeric flight ID (see: flights list).",
)
@click.option(
    "--licence-number",
    "-l",
    prompt="Licence number",
    help="Pilot's licence number, e.g. UK-10234.",
)
@click.option(
    "--role",
    "-r",
    type=click.Choice(["Captain", "First Officer"], case_sensitive=False),
    prompt="Role",
    help="Role to assign: Captain or 'First Officer'.",
)
def assign_pilot(flight_id, licence_number, role):
    """Assign a pilot to a flight as Captain or First Officer.

    Validates that the pilot exists, has no overlapping flights, and that the
    role is not already filled. Use 'flights available-pilots' to find eligible
    pilots first.
    """
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


@flights.command("details")
@click.argument("flight_id", type=int)
def flight_details(flight_id):
    """Show full details for a single flight including its assigned crew.

    FLIGHT_ID is the numeric flight ID (see: flights list).
    """
    with closing(get_connection()) as db:
        flight, crew = queries.get_flight_details(db, flight_id)

    if flight is None:
        raise click.ClickException(f"No flight found with ID {flight_id}.")

    click.echo(f"Flight:     {flight['flight_number']}  (ID {flight_id})")
    click.echo(f"Route:      {flight['departure_code']} -> {flight['arrival_code']}")
    click.echo(f"Departure:  {flight['departure_time']}")
    click.echo(f"Arrival:    {flight['arrival_time']}")
    click.echo(f"Duration:   {format_duration(flight['flight_time_minutes'])}")
    click.echo(f"Aircraft:   {flight['registration_number']}")
    click.echo(f"Status:     {flight['status']}")
    click.echo("")

    crew_rows = [
        [r["licence_number"], f"{r['first_name']} {r['last_name']}", r["role"]]
        for r in crew
    ]
    print_table(
        crew_rows,
        headers=["Licence Number", "Name", "Role"],
        empty_message="No crew assigned.",
    )


@flights.command("cancel")
@click.option(
    "--flight-id",
    "-f",
    type=int,
    prompt="Flight ID",
    help="Numeric flight ID (see: flights list).",
)
def cancel_flight(flight_id):
    """Cancel a flight. Only Scheduled or Delayed flights can be cancelled."""
    with closing(get_connection()) as db:
        updated = queries.cancel_flight(db, flight_id)

    if not updated:
        raise click.ClickException(
            f"Flight {flight_id} was not cancelled. "
            "It may not exist or its status does not allow cancellation "
            "(must be Scheduled or Delayed)."
        )
    click.echo(f"Flight {flight_id} cancelled.")


@flights.command("refresh-status")
def refresh_status():
    """Bulk-update flight statuses based on current UTC time.

    Marks flights as In Progress once departed and Completed once landed.
    Cancelled flights are never overwritten. Run this periodically to keep
    statuses accurate.
    """
    with closing(get_connection()) as db:
        in_progress, completed = queries.refresh_flight_statuses(db)

    click.echo(f"Marked {in_progress} flight(s) as In Progress.")
    click.echo(f"Marked {completed} flight(s) as Completed.")


@flights.command("unassign-pilot")
@click.option(
    "--flight-id",
    "-f",
    type=int,
    prompt="Flight ID",
    help="Numeric flight ID (see: flights list).",
)
@click.option(
    "--licence-number",
    "-l",
    prompt="Licence number",
    help="Pilot's licence number, e.g. UK-10234.",
)
def unassign_pilot(flight_id, licence_number):
    """Remove a pilot from a flight's crew."""
    with closing(get_connection()) as db:
        pilot = queries.get_pilot_by_licence(db, licence_number)
        if pilot is None:
            raise click.ClickException(
                f"No pilot found with licence number {licence_number!r}."
            )
        removed = queries.unassign_pilot_from_flight(db, flight_id, pilot["pilot_id"])

    if not removed:
        raise click.ClickException(
            f"Pilot {licence_number} is not assigned to flight {flight_id}."
        )
    name = f"{pilot['first_name']} {pilot['last_name']}"
    click.echo(f"Removed {name} ({licence_number}) from flight {flight_id}.")


@flights.command("delay")
@click.option(
    "--flight-id",
    "-f",
    type=int,
    prompt="Flight ID",
    help="Numeric flight ID (see: flights list).",
)
@click.option(
    "--minutes",
    "-m",
    type=int,
    prompt="Delay by (minutes)",
    help="Number of minutes to push the departure time forward. Must be positive.",
)
def delay_flight(flight_id, minutes):
    """Delay a flight by a given number of minutes.

    Shifts the departure time forward and sets status to Delayed. Only
    Scheduled or already Delayed flights can be delayed.
    """
    if minutes <= 0:
        raise click.ClickException("Delay must be a positive number of minutes.")

    with closing(get_connection()) as db:
        updated = queries.delay_flight(db, flight_id, minutes)

    if not updated:
        raise click.ClickException(
            f"Flight {flight_id} was not updated. "
            "It may not exist or its status does not allow delays "
            "(must be Scheduled or Delayed)."
        )
    click.echo(f"Flight {flight_id} delayed by {minutes} minutes.")


@flights.command("add")
def add_flight():
    """Add a new flight, prompting for all required details.

    Both airports must already exist (see: airports add). The aircraft must
    be registered (see: aircraft add). Flight duration is estimated from
    airport coordinates but can be overridden.
    """
    with closing(get_connection()) as db:
        departure_code = click.prompt("Departure airport code").upper()
        departure_airport = queries.get_airport_by_code(db, departure_code)
        if departure_airport is None:
            raise click.ClickException(
                f"Airport {departure_code!r} not found. Add it first with: airports add"
            )

        arrival_code = click.prompt("Arrival airport code").upper()
        arrival_airport = queries.get_airport_by_code(db, arrival_code)
        if arrival_airport is None:
            raise click.ClickException(
                f"Airport {arrival_code!r} not found. Add it first with: airports add"
            )

        registration = click.prompt("Aircraft registration").upper()
        aircraft = queries.get_aircraft_by_registration(db, registration)
        if aircraft is None:
            raise click.ClickException(f"Aircraft {registration!r} not found.")

        flight_number = click.prompt("Flight number").upper()
        departure_time = click.prompt("Departure time (YYYY-MM-DD HH:MM:SS)")

        estimated = estimate_flight_minutes(
            departure_airport["latitude"],
            departure_airport["longitude"],
            arrival_airport["latitude"],
            arrival_airport["longitude"],
        )
        flight_time_minutes = click.prompt(
            "Flight time (minutes)", default=estimated, type=int
        )

        flight_id = queries.add_flight(
            db,
            flight_number=flight_number,
            departure_airport_id=departure_airport["airport_id"],
            arrival_airport_id=arrival_airport["airport_id"],
            aircraft_id=aircraft["aircraft_id"],
            departure_time=departure_time,
            flight_time_minutes=flight_time_minutes,
        )

    click.echo(f"Added flight {flight_number} (ID {flight_id}).")


@flights.command("update")
@click.option(
    "--flight-id",
    "-f",
    type=int,
    prompt="Flight ID",
    help="Numeric flight ID (see: flights list).",
)
@click.option(
    "--flight-number",
    "-n",
    default=None,
    help="New flight number, e.g. BA214.",
)
@click.option(
    "--departure-time",
    "-d",
    default=None,
    help="New departure time in YYYY-MM-DD HH:MM:SS format (UTC).",
)
@click.option(
    "--flight-time-minutes",
    "-t",
    type=int,
    default=None,
    help="New flight duration in minutes (must be positive).",
)
@click.option(
    "--aircraft",
    "-a",
    default=None,
    help="New aircraft registration number, e.g. G-XWBA (must already exist).",
)
def update_flight(
    flight_id, flight_number, departure_time, flight_time_minutes, aircraft
):
    """Update a flight's details. Only supplied options are changed.

    To change crew assignments use 'flights assign-pilot' and
    'flights unassign-pilot'. Route (airports) cannot be changed here.
    """
    with closing(get_connection()) as db:
        flight = queries.get_flight_by_id(db, flight_id)
        if flight is None:
            raise click.ClickException(f"No flight found with ID {flight_id}.")

        aircraft_id = None
        if aircraft is not None:
            row = queries.get_aircraft_by_registration(db, aircraft)
            if row is None:
                raise click.ClickException(f"Aircraft {aircraft!r} not found.")
            aircraft_id = row["aircraft_id"]

        updated = queries.update_flight(
            db,
            flight_id,
            flight_number=flight_number.upper() if flight_number else None,
            departure_time=departure_time,
            flight_time_minutes=flight_time_minutes,
            aircraft_id=aircraft_id,
        )

    if not updated:
        click.echo("No changes made.")
    else:
        click.echo(f"Flight {flight_id} updated.")

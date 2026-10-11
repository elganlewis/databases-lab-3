from contextlib import closing

import click

import databases_lab_3.queries as queries
from databases_lab_3.utils import available_role, get_connection, print_table


@click.group()
def pilots():
    """Pilot commands."""


@pilots.command("list")
@click.option(
    "--licence",
    "-l",
    default=None,
    help="Filter by licence number, e.g. UK-12033.",
)
@click.option(
    "--name",
    "-n",
    default=None,
    help=(
        "Filter by pilot's full name, last name or first name e.g. Daniel Okafor, "
        "Okafor or Daniel."
    ),
)
def list_pilots(licence, name):
    """List all pilots."""
    with closing(get_connection()) as db:
        rows = queries.get_pilots(db, licence, name)

    table = [
        [
            row["licence_number"],
            f"{row['first_name']} {row['last_name']}",
            row["hire_date"] or "-",
            row["email"] or "-",
            row["phone_numbers"] or "-",
        ]
        for row in rows
    ]
    print_table(
        table,
        headers=["Licence Number", "Name", "Hire Date", "Email", "Phone Numbers"],
        empty_message="No pilots found.",
    )


@pilots.command()
@click.argument("licence_number")
def schedule(licence_number):
    """Get a given pilot's full schedule.

    LICENCE_NUMBER is the pilot's licence number, e.g. UK-10234.
    """
    with closing(get_connection()) as db:
        rows = queries.get_pilot_schedule(db, licence_number=licence_number)

    table = [
        [
            row["flight_number"],
            f"{row['departure_code']} -> {row['arrival_code']}",
            row["departure_time"],
            row["arrival_time"],
            row["role"],
            row["status"],
        ]
        for row in rows
    ]

    print_table(
        table,
        headers=[
            "Flight Number",
            "Departure -> Arrival",
            "Departure Time",
            "Arrival Time",
            "Role",
            "Status",
        ],
        empty_message="No flights found.",
    )


@pilots.command("assign")
@click.argument("flight_id", type=int)
@click.argument("licence_number")
@click.option(
    "--role",
    "-r",
    type=click.Choice(["Captain", "First Officer"], case_sensitive=False),
    required=True,
    help="Role to assign: Captain or 'First Officer'.",
)
def assign_pilot(flight_id, licence_number, role):
    """Assign a pilot to a flight.

    FLIGHT_ID is the numeric flight ID (see 'pilots available-flights').
    LICENCE_NUMBER is the pilot's licence number, e.g. UK-10234.
    """
    # Normalise role capitalisation to match DB values
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


@pilots.command("add")
def add_pilot():
    pass  # TODO: add add command


@pilots.command("remove")
def remove_pilot():
    pass  # TODO: add remove


@pilots.command("update")
def udpate_pilot():
    pass  # TODO: add update


@pilots.command("available-flights")
def available_flights():
    """Return flights that are available to be assigned to pilots."""
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
            "Available Role",
            "Status",
        ],
        empty_message="No flights found.",
    )

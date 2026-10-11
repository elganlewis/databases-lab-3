from contextlib import closing

import click

import databases_lab_3.queries as queries
from databases_lab_3.utils import get_connection, print_table


@click.group()
def pilots():
    """Pilot commands."""


@pilots.command("list")
def list_pilots():
    """List all pilots."""
    with closing(get_connection()) as db:
        rows = queries.get_pilots(db)

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
def assign_pilot():
    pass


@pilots.command("add")
def add_pilot():
    pass


@pilots.command("remove")
def remove_pilot():
    pass


@pilots.command("update")
def udpate_pilot():
    pass

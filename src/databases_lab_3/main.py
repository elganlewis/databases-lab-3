from contextlib import closing

import click
from tabulate import tabulate

from databases_lab_3 import queries
from databases_lab_3.db import get_connection


def print_table(rows, headers, empty_message="No results found."):
    """Print rows as a table, or a message if there are none."""
    if not rows:
        click.echo(empty_message)
        return
    click.echo(tabulate(rows, headers=headers, tablefmt="simple_outline"))


def format_duration(minutes):
    """Format a number of minutes as e.g. '1h 05m'."""
    return f"{minutes // 60}h {minutes % 60:02d}m"


@click.group()
def main():
    """Flight Management Database CLI."""


@main.group()
def flights():
    """Pilot commands."""


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
            "Flight Number",
            "Departure -> Arrival",
            "Departure Time",
            "Flight Length",
            "Status",
        ],
        empty_message="No flights found.",
    )


@main.group()
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


if __name__ == "__main__":
    main()

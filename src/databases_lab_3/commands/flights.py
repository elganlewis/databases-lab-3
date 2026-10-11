from contextlib import closing

import click

import databases_lab_3.queries as queries
from databases_lab_3.utils import format_duration, get_connection, print_table


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


@flights.command("delay")
def delay_flight():
    pass  # TODO: add delay


@flights.command("add")
def add_flight():
    pass  # TODO: add add command


@flights.command("update")
def update_flight():
    pass  # TODO: add update command

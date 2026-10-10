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


@main.command()
@click.option("--airport", "-a", default=None, help="Filter by airport code, e.g. LHR.")
@click.option(
    "--status", "-s", default=None, help="Filter by status code, e.g. completed."
)
def flights(airport, status):
    """Get a list of flight details."""
    with closing(get_connection()) as db:
        rows = queries.get_flights(db, airport=airport, status=status)

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


if __name__ == "__main__":
    main()

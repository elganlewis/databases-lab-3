from contextlib import closing

import click

import databases_lab_3.queries as queries
from databases_lab_3.utils import get_connection, print_table


@click.group()
def airports():
    """Airport commands."""


@airports.command("list")
@click.option("--wide", "-w", is_flag=True, help="Also show coordinates and elevation.")
@click.option(
    "--code",
    "-c",
    default=None,
    help="Filter by airport code, either iata or icao, e.g. DXB / OMDB.",
)
@click.option(
    "--country",
    "-C",
    default=None,
    help="Filter by country code, e.g. GB, US.",
)
def list_airports(wide, code, country):
    """List all airports."""
    with closing(get_connection()) as db:
        rows = queries.get_airports(db, code=code, country=country)

    headers = ["Airport", "City", "IATA / ICAO", "Country"]
    if wide:
        headers += ["Coordinates", "Elevation"]
    headers.append("Runways")

    table = []
    for row in rows:
        line = [
            row["airport_name"],
            row["city_name"],
            f"{row['iata_code'] or '-'} / {row['icao_code']}",
            row["country_code"],
        ]
        if wide:
            line += [
                f"{row['latitude']}, {row['longitude']}",
                f"{row['elevation_feet']} ft",
            ]
        line.append(row["runways"] or "-")
        table.append(line)

    print_table(table, headers=headers, empty_message="No airports found.")


@airports.command("add")
def add_airport():
    pass  # TODO: add command


@airports.command("remove")
def remove_airport():
    pass  # TODO: add remove


@airports.command("update")
def update_airport():
    pass  # TODO: add update

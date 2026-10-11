import sqlite3
from contextlib import closing

import click

import databases_lab_3.queries as queries
from databases_lab_3.utils import estimate_flight_minutes, get_connection, print_table


@click.group()
def airports():
    """Commands for managing airports and runways."""


@airports.command("list")
@click.option("--wide", "-w", is_flag=True, help="Also show coordinates and elevation.")
@click.option(
    "--code",
    "-c",
    default=None,
    help="Filter by IATA or ICAO code, e.g. LHR or EGLL.",
)
@click.option(
    "--country",
    "-C",
    default=None,
    help="Filter by ISO 3166-1 alpha-2 country code, e.g. GB, US.",
)
def list_airports(wide, code, country):
    """List airports with their codes, city, country and runways.

    Use --wide to also show coordinates and elevation.
    """
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
    """Add a new airport, prompting for all required details.

    IATA code is optional (small airfields may not have one). ICAO code is
    required and must be 4 characters. Timezone should be an IANA name,
    e.g. Europe/London. Coordinates: latitude -90 to 90, longitude -180 to 180.
    Add runways afterwards with 'airports add-runway'.
    """
    iata_code = (
        click.prompt("IATA code (3 letters, or leave blank)", default="").upper()
        or None
    )
    icao_code = click.prompt("ICAO code (4 letters)").upper()
    airport_name = click.prompt("Airport name")
    city_name = click.prompt("City")
    country_code = click.prompt("Country code (2 letters, e.g. GB)").upper()
    timezone = click.prompt("Timezone (e.g. Europe/London)")
    latitude = click.prompt("Latitude (-90 to 90)", type=float)
    longitude = click.prompt("Longitude (-180 to 180)", type=float)
    elevation_feet = click.prompt("Elevation (feet, can be negative)", type=int)

    with closing(get_connection()) as db:
        try:
            airport_id = queries.add_airport(
                db,
                iata_code=iata_code,
                icao_code=icao_code,
                airport_name=airport_name,
                city_name=city_name,
                country_code=country_code,
                timezone=timezone,
                latitude=latitude,
                longitude=longitude,
                elevation_feet=elevation_feet,
            )
        except sqlite3.IntegrityError as err:
            raise click.ClickException(f"Could not add airport: {err}") from err

    click.echo(f"Added airport {icao_code} (ID {airport_id}).")


@airports.command("update")
@click.option(
    "--code",
    "-c",
    prompt="Airport code (IATA or ICAO)",
    help="IATA or ICAO code identifying the airport to update.",
)
@click.option("--name", default=None, help="New airport name.")
@click.option("--city", default=None, help="New city name.")
@click.option(
    "--country",
    default=None,
    help="New ISO 3166-1 alpha-2 country code, e.g. GB.",
)
@click.option("--timezone", default=None, help="New IANA timezone, e.g. Europe/London.")
@click.option(
    "--latitude",
    type=float,
    default=None,
    help="New latitude (-90 to 90).",
)
@click.option(
    "--longitude",
    type=float,
    default=None,
    help="New longitude (-180 to 180).",
)
@click.option("--elevation-feet", type=int, default=None, help="New elevation in feet.")
def update_airport(
    code, name, city, country, timezone, latitude, longitude, elevation_feet
):
    """Update an airport's details. Only supplied options are changed."""
    with closing(get_connection()) as db:
        airport = queries.get_airport_by_code(db, code)
        if airport is None:
            raise click.ClickException(f"No airport found with code {code!r}.")

        updated = queries.update_airport(
            db,
            airport["airport_id"],
            airport_name=name,
            city_name=city,
            country_code=country.upper() if country else None,
            timezone=timezone,
            latitude=latitude,
            longitude=longitude,
            elevation_feet=elevation_feet,
        )

    if not updated:
        click.echo("No changes made.")
    else:
        click.echo(f"Airport {code.upper()} updated.")


@airports.command("remove")
@click.option(
    "--code",
    "-c",
    prompt="Airport code (IATA or ICAO)",
    help="IATA or ICAO code of the airport to remove.",
)
def remove_airport(code):
    """Remove an airport and all its runways. Fails if any flight uses it."""
    with closing(get_connection()) as db:
        airport = queries.get_airport_by_code(db, code)
        if airport is None:
            raise click.ClickException(f"No airport found with code {code!r}.")

        removed = queries.delete_airport(db, airport["airport_id"])

    if not removed:
        raise click.ClickException(
            f"Cannot remove {code.upper()}: it is used by one or more flights."
        )
    click.echo(f"Removed airport {code.upper()}.")


@airports.command("add-runway")
@click.option(
    "--code",
    "-c",
    prompt="Airport code (IATA or ICAO)",
    help="IATA or ICAO code of the airport.",
)
@click.option(
    "--designation",
    "-d",
    prompt="Runway designation (e.g. 09L)",
    help="Runway designation, e.g. 09L, 27R, 36. Must be unique at this airport.",
)
@click.option(
    "--length-m",
    "-l",
    type=int,
    prompt="Length (m)",
    help="Runway length in metres (must be positive).",
)
@click.option(
    "--surface",
    "-s",
    prompt="Surface (e.g. Asphalt)",
    help="Surface material, e.g. Asphalt, Concrete, Asphalt/Concrete.",
)
def add_runway(code, designation, length_m, surface):
    """Add a runway to an airport."""
    with closing(get_connection()) as db:
        airport = queries.get_airport_by_code(db, code)
        if airport is None:
            raise click.ClickException(f"No airport found with code {code!r}.")

        try:
            queries.add_runway(
                db, airport["airport_id"], designation.upper(), length_m, surface
            )
        except sqlite3.IntegrityError as err:
            raise click.ClickException(
                f"Runway {designation.upper()} already exists at {code.upper()}."
            ) from err

    click.echo(f"Added runway {designation.upper()} to {code.upper()}.")


@airports.command("update-runway")
@click.option(
    "--code",
    "-c",
    prompt="Airport code (IATA or ICAO)",
    help="IATA or ICAO code of the airport.",
)
@click.option(
    "--designation",
    "-d",
    prompt="Runway designation (e.g. 09L)",
    help="Designation of the runway to update, e.g. 09L.",
)
@click.option("--length-m", "-l", type=int, default=None, help="New length in metres.")
@click.option(
    "--surface",
    "-s",
    default=None,
    help="New surface type, e.g. Asphalt, Concrete, Asphalt/Concrete.",
)
def update_runway(code, designation, length_m, surface):
    """Update a runway's length and/or surface. Only supplied options are changed."""
    with closing(get_connection()) as db:
        airport = queries.get_airport_by_code(db, code)
        if airport is None:
            raise click.ClickException(f"No airport found with code {code!r}.")

        if queries.get_runway(db, airport["airport_id"], designation.upper()) is None:
            raise click.ClickException(
                f"Runway {designation.upper()} not found at {code.upper()}."
            )

        updated = queries.update_runway(
            db,
            airport["airport_id"],
            designation.upper(),
            length_m=length_m,
            surface=surface,
        )

    if not updated:
        click.echo("No changes made.")
    else:
        click.echo(f"Runway {designation.upper()} at {code.upper()} updated.")


@airports.command("distance")
@click.argument("code_a")
@click.argument("code_b")
def distance(code_a, code_b):
    """Show the estimated flight time between two airports.

    Uses the great-circle (shortest path) distance and an assumed cruising
    speed of 900 km/h. Both airports must exist in the database.

    CODE_A and CODE_B are IATA or ICAO codes, e.g. LHR JFK.
    """
    with closing(get_connection()) as db:
        airport_a = queries.get_airport_by_code(db, code_a)
        if airport_a is None:
            raise click.ClickException(f"No airport found with code {code_a!r}.")

        airport_b = queries.get_airport_by_code(db, code_b)
        if airport_b is None:
            raise click.ClickException(f"No airport found with code {code_b!r}.")

    minutes = estimate_flight_minutes(
        airport_a["latitude"],
        airport_a["longitude"],
        airport_b["latitude"],
        airport_b["longitude"],
    )
    hours, mins = divmod(minutes, 60)
    code_a, code_b = code_a.upper(), code_b.upper()

    click.echo(f"{code_a} -> {code_b}:  ~{hours}h {mins:02d}m estimated flight time")

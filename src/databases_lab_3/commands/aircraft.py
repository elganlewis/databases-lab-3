import sqlite3
from contextlib import closing

import click

import databases_lab_3.queries as queries
from databases_lab_3.utils import get_connection, print_table


@click.group()
def aircraft():
    """Commands for managing aircraft."""


@aircraft.command("list")
@click.option(
    "--registration",
    "-r",
    default=None,
    help="Filter by registration number, e.g. G-XWBA.",
)
@click.option(
    "--status",
    "-s",
    type=click.Choice(["Active", "In Maintenance", "Retired"], case_sensitive=False),
    default=None,
    help="Filter by status: Active, 'In Maintenance' or Retired.",
)
def list_aircraft(registration, status):
    """List aircraft with registration, model, capacity,
    range and runway requirements."""
    with closing(get_connection()) as db:
        rows = queries.get_aircraft(db, registration=registration, status=status)

    table = [
        [
            row["registration_number"],
            row["model"],
            row["manufacturer"],
            row["capacity"],
            row["range_km"],
            row["min_runway_m"],
            row["year_manufactured"],
            row["status"],
        ]
        for row in rows
    ]
    print_table(
        table,
        headers=[
            "Registration",
            "Model",
            "Manufacturer",
            "Capacity",
            "Range (km)",
            "Min Runway (m)",
            "Year",
            "Status",
        ],
        empty_message="No aircraft found.",
    )


@aircraft.command("add")
def add_aircraft():
    """Add a new aircraft, prompting for all required details.

    Min runway (m) is the shortest runway the aircraft can use — used to
    check compatibility with airports when assigning flights.
    Status defaults to Active.
    """
    registration = click.prompt("Registration number").upper()
    model = click.prompt("Model")
    manufacturer = click.prompt("Manufacturer")
    capacity = click.prompt("Passenger capacity", type=int)
    range_km = click.prompt("Range (km)", type=int)
    min_runway_m = click.prompt("Minimum runway length (m)", type=int)
    year_manufactured = click.prompt("Year manufactured (1950–2100)", type=int)

    with closing(get_connection()) as db:
        aircraft_id = queries.add_aircraft(
            db,
            registration_number=registration,
            model=model,
            manufacturer=manufacturer,
            capacity=capacity,
            range_km=range_km,
            min_runway_m=min_runway_m,
            year_manufactured=year_manufactured,
        )

    click.echo(f"Added aircraft {registration} (ID {aircraft_id}).")


@aircraft.command("update")
@click.option(
    "--registration",
    "-r",
    prompt="Registration number",
    help="Registration number of the aircraft to update, e.g. G-XWBA.",
)
@click.option("--model", "-m", default=None, help="New model name.")
@click.option("--manufacturer", default=None, help="New manufacturer name.")
@click.option(
    "--capacity",
    "-c",
    type=int,
    default=None,
    help="New passenger capacity (must be positive).",
)
@click.option(
    "--range-km",
    type=int,
    default=None,
    help="New maximum range in km (must be positive).",
)
@click.option(
    "--min-runway-m",
    type=int,
    default=None,
    help="New minimum runway length in metres (must be positive).",
)
@click.option(
    "--year-manufactured",
    type=int,
    default=None,
    help="New year manufactured (1950–2100).",
)
@click.option(
    "--status",
    "-s",
    type=click.Choice(["Active", "In Maintenance", "Retired"], case_sensitive=False),
    default=None,
    help="New status: Active, 'In Maintenance' or Retired.",
)
def update_aircraft(
    registration,
    model,
    manufacturer,
    capacity,
    range_km,
    min_runway_m,
    year_manufactured,
    status,
):
    """Update an aircraft's details. Only supplied options are changed."""
    with closing(get_connection()) as db:
        rows = queries.get_aircraft(db, registration=registration)
        if not rows:
            raise click.ClickException(
                f"No aircraft found with registration {registration!r}."
            )

        updated = queries.update_aircraft(
            db,
            rows[0]["aircraft_id"],
            model=model,
            manufacturer=manufacturer,
            capacity=capacity,
            range_km=range_km,
            min_runway_m=min_runway_m,
            year_manufactured=year_manufactured,
            status=status,
        )

    if not updated:
        click.echo("No changes made.")
    else:
        click.echo(f"Aircraft {registration} updated.")


@aircraft.command("remove")
@click.option(
    "--registration",
    "-r",
    prompt="Registration number",
    help="Registration number of the aircraft to remove, e.g. G-XWBA.",
)
def remove_aircraft(registration):
    """Remove an aircraft. Fails if it is assigned to any flight."""
    with closing(get_connection()) as db:
        rows = queries.get_aircraft(db, registration=registration)
        if not rows:
            raise click.ClickException(
                f"No aircraft found with registration {registration!r}."
            )

        try:
            removed = queries.delete_aircraft(db, rows[0]["aircraft_id"])
        except sqlite3.IntegrityError as err:
            raise click.ClickException(
                f"Cannot remove {registration}: it is assigned to one or more flights."
            ) from err

    if not removed:
        raise click.ClickException(
            f"No aircraft found with registration {registration!r}."
        )
    click.echo(f"Removed aircraft {registration}.")

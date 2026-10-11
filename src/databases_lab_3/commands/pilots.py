import sqlite3
from contextlib import closing

import click

import databases_lab_3.queries as queries
from databases_lab_3.utils import get_connection, print_table


@click.group()
def pilots():
    """Commands for managing pilots and their assignments."""


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
        "Filter by full name, last name or first name, "
        "e.g. 'Daniel Okafor', 'Okafor' or 'Daniel'."
    ),
)
def list_pilots(licence, name):
    """List pilots with their licence number, hire date, email and phone numbers."""
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
    """Show all flights (past and future) assigned to a pilot.

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


@pilots.command("add")
def add_pilot():
    """Add a new pilot, prompting for all details.

    Licence number must be unique. Hire date (YYYY-MM-DD) and email are
    optional. Phone numbers can be added afterwards with 'pilots add-phone'.
    """
    licence_number = click.prompt("Licence number")
    first_name = click.prompt("First name")
    last_name = click.prompt("Last name")
    hire_date = (
        click.prompt("Hire date (YYYY-MM-DD, or leave blank)", default="") or None
    )
    email = click.prompt("Email (or leave blank)", default="") or None

    with closing(get_connection()) as db:
        try:
            pilot_id = queries.add_pilot(
                db,
                licence_number=licence_number,
                first_name=first_name,
                last_name=last_name,
                hire_date=hire_date,
                email=email,
            )
        except sqlite3.IntegrityError as err:
            raise click.ClickException(f"Could not add pilot: {err}") from err

    click.echo(f"Added pilot {first_name} {last_name} (ID {pilot_id}).")


@pilots.command("update")
@click.option(
    "--licence", "-l", prompt="Licence number",
    help="Licence number of the pilot to update, e.g. UK-10234.",
)
@click.option("--first-name", default=None, help="New first name.")
@click.option("--last-name", default=None, help="New last name.")
@click.option("--hire-date", default=None, help="New hire date (YYYY-MM-DD).")
@click.option("--email", default=None, help="New email address.")
def update_pilot(licence, first_name, last_name, hire_date, email):
    """Update a pilot's details. Only supplied options are changed."""
    with closing(get_connection()) as db:
        pilot = queries.get_pilot_by_licence(db, licence)
        if pilot is None:
            raise click.ClickException(
                f"No pilot found with licence number {licence!r}."
            )

        updated = queries.update_pilot(
            db,
            pilot["pilot_id"],
            first_name=first_name,
            last_name=last_name,
            hire_date=hire_date,
            email=email,
        )

    if not updated:
        click.echo("No changes made.")
    else:
        click.echo(f"Pilot {licence} updated.")


@pilots.command("remove")
@click.option(
    "--licence", "-l", prompt="Licence number",
    help="Licence number of the pilot to remove, e.g. UK-10234.",
)
def remove_pilot(licence):
    """Remove a pilot. Fails if the pilot is assigned to any flight."""
    with closing(get_connection()) as db:
        pilot = queries.get_pilot_by_licence(db, licence)
        if pilot is None:
            raise click.ClickException(
                f"No pilot found with licence number {licence!r}."
            )

        try:
            queries.delete_pilot(db, pilot["pilot_id"])
        except sqlite3.IntegrityError as err:
            raise click.ClickException(
                f"Cannot remove {licence}: pilot is assigned to one or more flights."
            ) from err

    name = f"{pilot['first_name']} {pilot['last_name']}"
    click.echo(f"Removed pilot {name} ({licence}).")


@pilots.command("add-phone")
@click.option(
    "--licence", "-l", prompt="Licence number",
    help="Licence number of the pilot, e.g. UK-10234.",
)
@click.option(
    "--phone", "-p", prompt="Phone number",
    help="Phone number to add, e.g. +44 7700 900123. A pilot may have multiple.",
)
def add_phone(licence, phone):
    """Add a phone number to a pilot."""
    with closing(get_connection()) as db:
        pilot = queries.get_pilot_by_licence(db, licence)
        if pilot is None:
            raise click.ClickException(
                f"No pilot found with licence number {licence!r}."
            )

        try:
            queries.add_pilot_phone(db, pilot["pilot_id"], phone)
        except sqlite3.IntegrityError as err:
            raise click.ClickException(
                f"Phone number {phone!r} is already registered to this pilot."
            ) from err

    click.echo(f"Added phone number {phone} to pilot {licence}.")


@pilots.command("remove-phone")
@click.option(
    "--licence", "-l", prompt="Licence number",
    help="Licence number of the pilot, e.g. UK-10234.",
)
@click.option(
    "--phone", "-p", prompt="Phone number",
    help="Exact phone number to remove.",
)
def remove_phone(licence, phone):
    """Remove a phone number from a pilot."""
    with closing(get_connection()) as db:
        pilot = queries.get_pilot_by_licence(db, licence)
        if pilot is None:
            raise click.ClickException(
                f"No pilot found with licence number {licence!r}."
            )

        removed = queries.delete_pilot_phone(db, pilot["pilot_id"], phone)

    if not removed:
        raise click.ClickException(
            f"Phone number {phone!r} is not registered to pilot {licence}."
        )
    click.echo(f"Removed phone number {phone} from pilot {licence}.")

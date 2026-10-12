from contextlib import closing

import click

from databases_lab_3.commands.aircraft import aircraft
from databases_lab_3.commands.airports import airports
from databases_lab_3.commands.flights import flights
from databases_lab_3.commands.pilots import pilots
from databases_lab_3.utils import get_connection, print_table


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Flight Management Database CLI."""
    if ctx.invoked_subcommand is None:
        _show_dashboard()


def _show_dashboard():
    try:
        with closing(get_connection()) as db:
            counts = db.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM flight)   AS flights,
                    (SELECT COUNT(*) FROM pilot)    AS pilots,
                    (SELECT COUNT(*) FROM aircraft) AS aircraft,
                    (SELECT COUNT(*) FROM airport)  AS airports
                """
            ).fetchone()

            upcoming = db.execute(
                """
                SELECT flight_number,
                       departure_code || ' -> ' || arrival_code AS route,
                       departure_time, status
                FROM flight_details
                WHERE status IN ('Scheduled', 'Delayed')
                  AND departure_time >= datetime('now')
                ORDER BY departure_time
                LIMIT 5
                """
            ).fetchall()

            needs_crew = db.execute(
                """
                SELECT COUNT(*) AS n FROM (
                    SELECT fd.flight_id
                    FROM flight_details fd
                    LEFT JOIN flight_crew fc ON fc.flight_id = fd.flight_id
                    LEFT JOIN pilot p        ON p.pilot_id   = fc.pilot_id
                    WHERE fd.status IN ('Scheduled', 'Delayed')
                    GROUP BY fd.flight_id
                    HAVING MAX(CASE WHEN fc.role = 'Captain'       THEN 1 END) IS NULL
                        OR MAX(CASE WHEN fc.role = 'First Officer' THEN 1 END) IS NULL
                )
                """
            ).fetchone()["n"]

    except click.ClickException as e:
        e.show()
        return

    click.echo(click.style(" Flight Management Database", bold=True))
    click.echo("")
    click.echo(
        f" Flights: {counts['flights']:<6} Pilots: {counts['pilots']:<6}"
        f" Aircraft: {counts['aircraft']:<6} Airports: {counts['airports']:<4}"
    )
    click.echo("")

    if needs_crew:
        click.echo(
            f"  ⚠  {needs_crew} scheduled flight(s) still need crew — run:"
            " flights needs-crew"
        )
        click.echo("")

    if upcoming:
        click.echo("  Upcoming flights:")
        print_table(
            [
                [r["flight_number"], r["route"], r["departure_time"], r["status"]]
                for r in upcoming
            ],
            headers=["Flight", "Route", "Departure", "Status"],
        )
    else:
        click.echo("  No upcoming scheduled flights.")

    click.echo("")
    click.echo(click.style("  Common commands", bold=True))
    click.echo("  ─────────────────────────────────────────────────────")
    click.echo("  Add a new flight        flightdb flights add")
    click.echo(
        "  View flights"
        "            flightdb flights list [-D LHR] [-s Scheduled] [-d DATE]"
    )
    click.echo("  Update flight info      flightdb flights update")
    click.echo("  Assign pilot to flight  flightdb flights assign-pilot")
    click.echo("  View pilot schedule     flightdb pilots schedule <LICENCE>")
    click.echo("  View destinations       flightdb airports list [--wide]")
    click.echo("  Update destination      flightdb airports update")
    click.echo("  ─────────────────────────────────────────────────────")
    click.echo("  Run any command with --help for full usage details.")


main.add_command(aircraft)
main.add_command(airports)
main.add_command(flights)
main.add_command(pilots)

if __name__ == "__main__":
    main()

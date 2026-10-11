import click

from databases_lab_3.airports import airports
from databases_lab_3.flights import flights
from databases_lab_3.pilots import pilots


@click.group()
def main():
    """Flight Management Database CLI."""


main.add_command(flights)
main.add_command(airports)
main.add_command(pilots)

if __name__ == "__main__":
    main()

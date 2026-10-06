import click

@click.group()
def main():
    """My awesome CLI tool built with uv and click."""
    pass

@main.command()
@click.option("--name", default="World", help="The person to greet.")
def hello(name):
    """Greet someone."""
    click.echo(f"Hello, {name}!")

if __name__ == "__main__":
    main()
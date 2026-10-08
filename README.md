# Databases Lab Sheet 3

## Setup

This project requires Python 3.13 or later and [uv](https://docs.astral.sh/uv/getting-started/installation/).

Clone the repository, open a terminal in the project directory, and sync dependencies:

```bash
uv sync
```

This creates a `.venv` virtual environment and installs the project and development tools.

To run commands without the `uv run` prefix, activate the virtual environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.\.venv\Scripts\activate.ps1

# Windows (Command Prompt)
.venv\Scripts\activate.bat
```

With the environment activated, you can run commands like `flightdb`, `ruff check .`, or `ruff format .` directly.

## Using the CLI

You can run CLI commands either via `uv run` or directly when your virtual environment is active:

```bash
# Show available commands and options
uv run flightdb --help

# Run a command
uv run flightdb hello --name World
```

## GitHub Codespaces

You can also work on this repository in [GitHub Codespaces](https://docs.github.com/en/codespaces). The configuration at `.devcontainer/devcontainer.json` installs `uv` and runs `uv sync` automatically when the container is created.

Once the Codespace is ready, run `uv run flightdb` or activate `.venv` as described above to start using the CLI.

## Linting and Formatting

Check and format the codebase using [Ruff](https://docs.astral.sh/ruff/):

```bash
uv run ruff check .
uv run ruff format .
```

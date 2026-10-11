# Flight Management Database

A command-line application for managing airline flights, pilots, airports and aircraft, backed by SQLite.

## Requirements

- Python 3.13 or later
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Setup

Clone the repository, open a terminal in the project root, and sync dependencies:

```bash
uv sync
```

This creates a `.venv` virtual environment and installs the project and all development tools.

### Activate the virtual environment (optional)

To run commands without the `uv run` prefix:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.\.venv\Scripts\activate.ps1

# Windows (Command Prompt)
.venv\Scripts\activate.bat
```

With the environment activated, `flightdb`, `ruff`, and `pytest` can be called directly.

### GitHub Codespaces

The `.devcontainer/devcontainer.json` configuration installs `uv` and runs `uv sync` automatically. Once the Codespace is ready, activate `.venv` as above or prefix commands with `uv run`.

---

## Database setup

The database file is `flight_management.db` in the project root. **Commands must be run from the project root** or the file will not be found.

Create the schema and load sample data:

```bash
sqlite3 flight_management.db < flight_db_create_tables.sql
sqlite3 flight_management.db < flight_db_sample_data.sql
```

`flight_db_create_tables.sql` drops and recreates every table and the `flight_details` view.  
`flight_db_sample_data.sql` clears all tables first, so it is safe to re-run to reset the data.

To reset to a clean state at any time, just run both commands again.

---

## Using the CLI

Run `flightdb` with no arguments to open the dashboard, which shows live counts, any flights missing crew, and upcoming departures:

```bash
uv run flightdb
```

Every command group and subcommand accepts `--help`:

```bash
uv run flightdb --help
uv run flightdb flights --help
uv run flightdb flights list --help
```

### Command groups

| Group | Purpose |
|---|---|
| `flights` | Manage flights and crew assignments |
| `pilots` | Manage pilot records and phone numbers |
| `airports` | Manage airports and runways |
| `aircraft` | Manage aircraft records |

---

### `flights`

```
flightdb flights list              # all flights; filter with -D, -A, -s, -x, -d
flightdb flights details <id>      # full details + crew for one flight
flightdb flights needs-crew        # flights missing a Captain or First Officer
flightdb flights crew <id>         # crew assigned to a flight
flightdb flights available-pilots <id>   # pilots free to work this flight
flightdb flights assign-pilot      # assign a pilot (prompts; validates conflicts)
flightdb flights unassign-pilot    # remove a pilot from a flight
flightdb flights add               # add a flight (duration estimated from coordinates)
flightdb flights update            # update flight fields
flightdb flights delay             # shift departure time + set status to Delayed
flightdb flights cancel            # set status to Cancelled
flightdb flights refresh-status    # bulk-update In Progress / Completed from UTC time
```

**Filtering `flights list`**

```bash
# Flights from LHR
uv run flightdb flights list --departure-airport LHR

# Scheduled and Delayed flights on a specific date
uv run flightdb flights list -s scheduled -s delayed -d 2026-10-11

# Everything except cancelled and completed
uv run flightdb flights list -x cancelled -x completed
```

**Delaying a flight**

```bash
uv run flightdb flights delay --flight-id 3 --minutes 90
```

**Assigning a pilot**

```bash
uv run flightdb flights assign-pilot
# Prompts for flight ID, pilot licence number and role (Captain / First Officer).
# Validates that the pilot has no scheduling conflict and the role is not already filled.
```

---

### `pilots`

```
flightdb pilots list               # all pilots; filter with --licence or --name
flightdb pilots schedule <licence> # all flights (past and future) for a pilot
flightdb pilots add                # add a pilot (hire date and email optional)
flightdb pilots update             # update pilot fields
flightdb pilots remove             # delete a pilot (blocked if assigned to a flight)
flightdb pilots add-phone          # add a phone number
flightdb pilots remove-phone       # remove a phone number
```

**Finding a pilot**

```bash
uv run flightdb pilots list --name "Alice Smith"
uv run flightdb pilots list --licence UK-00001
```

**Viewing a pilot's schedule**

```bash
uv run flightdb pilots schedule UK-00001
```

---

### `airports`

```
flightdb airports list             # all airports; --wide for coordinates
flightdb airports add              # add an airport (IATA code optional)
flightdb airports update           # update airport fields
flightdb airports remove           # delete an airport (blocked if used by a flight)
flightdb airports add-runway       # add a runway to an airport
flightdb airports update-runway    # update runway length and/or surface
flightdb airports distance <A> <B> # great-circle distance + estimated flight time
```

**Examples**

```bash
# Airports in Great Britain
uv run flightdb airports list --country GB

# Distance and estimated flight time between two airports
uv run flightdb airports distance LHR JFK

# Add a runway to an existing airport
uv run flightdb airports add-runway
```

---

### `aircraft`

```
flightdb aircraft list             # all aircraft; filter by --registration or --status
flightdb aircraft add              # add an aircraft
flightdb aircraft update           # update aircraft fields (model, status, etc.)
flightdb aircraft remove           # delete an aircraft (blocked if assigned to a flight)
```

**Filtering by status**

```bash
uv run flightdb aircraft list --status Active
uv run flightdb aircraft list --status "In Maintenance"
```

---

## Project layout

```
.
├── flight_db_create_tables.sql   # Schema (drops and recreates all tables)
├── flight_db_sample_data.sql     # Sample data (safe to re-run)
├── flight_db_queries.sql         # Reference SQL for each menu operation
├── src/databases_lab_3/
│   ├── main.py                   # Entry point and dashboard
│   ├── utils.py                  # Shared helpers (formatting, connection, haversine)
│   ├── commands/
│   │   ├── flights.py
│   │   ├── pilots.py
│   │   ├── airports.py
│   │   └── aircraft.py
│   └── queries/
│       ├── __init__.py           # Re-exports all query functions
│       ├── flights.py
│       ├── pilots.py
│       ├── airports.py
│       └── aircraft.py
└── tests/
    ├── conftest.py               # In-memory DB fixture and seed helpers
    ├── test_utils.py
    ├── test_queries_aircraft.py
    ├── test_queries_airports.py
    ├── test_queries_pilots.py
    └── test_queries_flights.py
```

---

## Tests

Run the full test suite:

```bash
uv run pytest
```

Run with verbose output:

```bash
uv run pytest -v
```

Tests use an in-memory SQLite database and do not touch `flight_management.db`.

---

## Linting and formatting

```bash
uv run ruff check .
uv run ruff format .
```

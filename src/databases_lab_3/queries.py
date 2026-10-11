"""SQL queries. Each function takes an open connection and returns rows."""


def _placeholders(values):
    """Return '?, ?, ?' with one placeholder per value, for use in IN (...)."""
    return ", ".join("?" * len(values))


def get_flights(
    db,
    departure_airport=None,
    arrival_airport=None,
    status=(),
    exclude_status=(),
    date=None,
):
    """Return flights, optionally filtered by departure airport, arrival
    airport, status (any of), excluded statuses (none of) and/or departure
    date ('YYYY-MM-DD', UTC)."""
    query = """
        SELECT flight_id, flight_number, departure_code, arrival_code,
               departure_time, flight_time_minutes, status
        FROM flight_details
    """
    conditions = []
    params = []
    if departure_airport is not None:
        conditions.append("departure_code = ?")
        params.append(departure_airport.upper())
    if arrival_airport is not None:
        conditions.append("arrival_code = ?")
        params.append(arrival_airport.upper())
    if status:
        conditions.append(f"LOWER(status) IN ({_placeholders(status)})")
        params += [s.lower() for s in status]
    if exclude_status:
        conditions.append(f"LOWER(status) NOT IN ({_placeholders(exclude_status)})")
        params += [s.lower() for s in exclude_status]
    if date is not None:
        # departure_time is 'YYYY-MM-DD HH:MM:SS'; date() keeps just the day part.
        conditions.append("date(departure_time) = ?")
        params.append(date)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY departure_time"

    return db.execute(query, params).fetchall()


def get_pilot_schedule(db, licence_number):
    """Return a pilots's schedule from a given licence number"""
    query = """
        SELECT p.first_name, p.last_name, p.licence_number, fd.flight_number,
            fd.departure_code, fd.arrival_code,
            fd.departure_time, fd.arrival_time, fc.role, fd.status
        FROM pilot p
        JOIN flight_crew fc    ON fc.pilot_id  = p.pilot_id
        JOIN flight_details fd ON fd.flight_id = fc.flight_id
        WHERE p.licence_number = ?
        ORDER BY fd.departure_time;
    """

    params = [licence_number]

    return db.execute(query, params).fetchall()


def get_pilots(db, licence, name):
    """Return all pilots, with their phone numbers joined into one string.
    Filter by licence number, full name, first name or last name
    """
    query = """
        SELECT p.licence_number, p.first_name, p.last_name, p.hire_date, p.email,
               GROUP_CONCAT(pp.phone_number, ', ') AS phone_numbers
        FROM pilot p
        LEFT JOIN pilot_phone pp ON pp.pilot_id = p.pilot_id
    """

    conditions = []
    params = []
    if licence is not None:
        conditions.append("p.licence_number = ?")
        params.append(licence)
    if name is not None:
        conditions.append(
            "(concat(LOWER(p.first_name), ' '"
            ", LOWER(p.last_name)) = LOWER(?) OR LOWER(p.first_name)=LOWER(?)"
            "OR LOWER(p.last_name)=LOWER(?))"
        )
        params += [name, name, name]
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += """
        GROUP BY p.pilot_id
        ORDER BY p.last_name, p.first_name
    """
    return db.execute(query, params).fetchall()


def get_airports(db, code=None, country=None):
    """Return airports, with their runways (one per line) and lengths,
    optionally filtered by IATA/ICAO code and/or country code."""
    query = """
        SELECT a.airport_id, a.iata_code, a.icao_code, a.airport_name,
               a.city_name, a.country_code, a.timezone,
               a.latitude, a.longitude, a.elevation_feet,
               -- char(10) is a newline, so tabulate shows one runway per line
               GROUP_CONCAT(
                   r.runway_designation || ' (' || r.length_m || ' m)', char(10)
               ) AS runways
        FROM airport a
        LEFT JOIN runway r ON r.airport_id = a.airport_id
    """

    conditions = []
    params = []
    if code is not None:
        conditions.append("(a.iata_code = ? OR a.icao_code = ?)")
        params += [code.upper(), code.upper()]
    if country is not None:
        conditions.append("a.country_code = ?")
        params.append(country.upper())
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += """
        GROUP BY a.airport_id
        ORDER BY a.country_code, a.city_name
    """
    return db.execute(query, params).fetchall()


def get_available_flights(db):
    """Return flights that have unassigned crew roles
    (missing Captain or First Officer)."""
    query = """
        SELECT fd.flight_id, fd.flight_number, fd.departure_code, fd.arrival_code,
            fd.departure_time, fd.arrival_time, fd.flight_time_minutes, fd.status,
            fd.registration_number,
            MAX(CASE WHEN fc.role = 'Captain'
                THEN p.first_name || ' ' || p.last_name END) AS captain,
            MAX(CASE WHEN fc.role = 'Captain'
                THEN p.licence_number END) AS captain_licence_number,
            MAX(CASE WHEN fc.role = 'First Officer'
                THEN p.first_name || ' ' || p.last_name END) AS first_officer,
            MAX(CASE WHEN fc.role = 'First Officer'
                THEN p.licence_number END) AS first_officer_licence_number
        FROM flight_details fd
        LEFT JOIN flight_crew fc ON fc.flight_id = fd.flight_id
        LEFT JOIN pilot p        ON p.pilot_id   = fc.pilot_id
        GROUP BY fd.flight_id
        HAVING first_officer IS NULL OR captain IS NULL
        ORDER BY fd.departure_time;
    """
    return db.execute(query).fetchall()


get_avaliable_flights = get_available_flights


def get_available_pilots(db, flight_id):
    """Return pilots with no scheduling conflict for the given flight."""
    query = """
        SELECT p.pilot_id, p.licence_number, p.first_name, p.last_name
        FROM pilot p
        WHERE p.pilot_id NOT IN (
            SELECT fc.pilot_id
            FROM flight_crew fc
            JOIN flight_details fd     ON fd.flight_id = fc.flight_id
            JOIN flight_details target ON target.flight_id = ?
            WHERE fd.departure_time < target.arrival_time
              AND fd.arrival_time   > target.departure_time
        )
        ORDER BY p.last_name, p.first_name
    """
    return db.execute(query, (flight_id,)).fetchall()


def get_flight_crew(db, flight_id):
    """Return pilots assigned to a flight, ordered by role."""
    query = """
        SELECT p.pilot_id, p.licence_number, p.first_name, p.last_name, fc.role
        FROM flight_crew fc
        JOIN pilot p ON p.pilot_id = fc.pilot_id
        WHERE fc.flight_id = ?
        ORDER BY fc.role
    """
    return db.execute(query, (flight_id,)).fetchall()


def get_pilot_by_licence(db, licence_number):
    """Return a pilot row for the given licence number, or None."""
    return db.execute(
        "SELECT pilot_id, first_name, last_name FROM pilot WHERE licence_number = ?",
        (licence_number,),
    ).fetchone()


def check_pilot_conflict(db, pilot_id, flight_id):
    """Return rows of conflicting flights if the pilot is already scheduled
    during the target flight's window (no rows = safe to assign)."""
    query = """
        SELECT fd.flight_number, fd.departure_time, fd.arrival_time
        FROM flight_crew fc
        JOIN flight_details fd     ON fd.flight_id = fc.flight_id
        JOIN flight_details target ON target.flight_id = ?
        WHERE fc.pilot_id = ?
          AND fd.flight_id <> target.flight_id
          AND fd.departure_time < target.arrival_time
          AND fd.arrival_time   > target.departure_time
    """
    return db.execute(query, (flight_id, pilot_id)).fetchall()


def check_role_taken(db, flight_id, role):
    """Return the count of pilots already assigned to this role on the flight."""
    row = db.execute(
        "SELECT COUNT(*) AS n FROM flight_crew WHERE flight_id = ? AND role = ?",
        (flight_id, role),
    ).fetchone()
    return row["n"]


def assign_pilot_to_flight(db, flight_id, pilot_id, role):
    """Insert a flight_crew row assigning the pilot to the flight."""
    db.execute(
        "INSERT INTO flight_crew (flight_id, pilot_id, role) VALUES (?, ?, ?)",
        (flight_id, pilot_id, role),
    )
    db.commit()

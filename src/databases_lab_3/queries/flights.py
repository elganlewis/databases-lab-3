"""Flight and flight-crew queries."""


def _placeholders(values):
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
        conditions.append("date(departure_time) = ?")
        params.append(date)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY departure_time"
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


def get_flight_by_id(db, flight_id):
    """Return a single flight row from flight_details, or None."""
    return db.execute(
        "SELECT * FROM flight_details WHERE flight_id = ?",
        (flight_id,),
    ).fetchone()


def get_flight_details(db, flight_id):
    """Return full details for a single flight including crew."""
    flight = db.execute(
        "SELECT * FROM flight_details WHERE flight_id = ?", (flight_id,)
    ).fetchone()
    crew = db.execute(
        """
        SELECT p.licence_number, p.first_name, p.last_name, fc.role
        FROM flight_crew fc
        JOIN pilot p ON p.pilot_id = fc.pilot_id
        WHERE fc.flight_id = ?
        ORDER BY fc.role
        """,
        (flight_id,),
    ).fetchall()
    return flight, crew


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


def add_flight(
    db,
    flight_number,
    departure_airport_id,
    arrival_airport_id,
    aircraft_id,
    departure_time,
    flight_time_minutes,
):
    """Insert a new flight and return its flight_id."""
    cursor = db.execute(
        """
        INSERT INTO flight
            (flight_number, departure_airport_id, arrival_airport_id,
             aircraft_id, departure_time, flight_time_minutes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            flight_number,
            departure_airport_id,
            arrival_airport_id,
            aircraft_id,
            departure_time,
            flight_time_minutes,
        ),
    )
    db.commit()
    return cursor.lastrowid


def update_flight(
    db,
    flight_id,
    flight_number=None,
    departure_time=None,
    flight_time_minutes=None,
    aircraft_id=None,
):
    """Update editable fields on a flight. Only non-None values are applied."""
    fields = []
    params = []
    if flight_number is not None:
        fields.append("flight_number = ?")
        params.append(flight_number)
    if departure_time is not None:
        fields.append("departure_time = ?")
        params.append(departure_time)
    if flight_time_minutes is not None:
        fields.append("flight_time_minutes = ?")
        params.append(flight_time_minutes)
    if aircraft_id is not None:
        fields.append("aircraft_id = ?")
        params.append(aircraft_id)
    if not fields:
        return 0
    params.append(flight_id)
    cursor = db.execute(
        f"UPDATE flight SET {', '.join(fields)} WHERE flight_id = ?", params
    )
    db.commit()
    return cursor.rowcount


def delay_flight(db, flight_id, minutes):
    """Shift a flight's departure time forward and mark it Delayed.
    Only updates flights that are Scheduled or already Delayed.
    Returns the number of rows updated (0 = flight not found or wrong status)."""
    cursor = db.execute(
        """
        UPDATE flight
        SET departure_time = datetime(departure_time, ? || ' minutes'),
            status         = 'Delayed'
        WHERE flight_id = ?
          AND status IN ('Scheduled', 'Delayed')
        """,
        (minutes, flight_id),
    )
    db.commit()
    return cursor.rowcount


def cancel_flight(db, flight_id):
    """Cancel a flight. Only updates flights that are Scheduled or Delayed.
    Returns the number of rows updated (0 = not found or wrong status)."""
    cursor = db.execute(
        """
        UPDATE flight SET status = 'Cancelled'
        WHERE flight_id = ? AND status IN ('Scheduled', 'Delayed')
        """,
        (flight_id,),
    )
    db.commit()
    return cursor.rowcount


def refresh_flight_statuses(db):
    """Mark departed flights as In Progress and landed flights as Completed.
    Returns (in_progress_count, completed_count)."""
    in_progress = db.execute(
        """
        UPDATE flight SET status = 'In Progress'
        WHERE status IN ('Scheduled', 'Delayed')
          AND departure_time <= datetime('now')
          AND datetime(
            departure_time, '+' || flight_time_minutes || ' minutes'
          ) > datetime('now')
        """
    ).rowcount
    completed = db.execute(
        """
        UPDATE flight SET status = 'Completed'
        WHERE status IN ('Scheduled', 'Delayed', 'In Progress')
          AND datetime(
              departure_time, '+' || flight_time_minutes || ' minutes'
          ) <= datetime('now')
        """
    ).rowcount
    db.commit()
    return in_progress, completed


def assign_pilot_to_flight(db, flight_id, pilot_id, role):
    """Insert a flight_crew row assigning the pilot to the flight."""
    db.execute(
        "INSERT INTO flight_crew (flight_id, pilot_id, role) VALUES (?, ?, ?)",
        (flight_id, pilot_id, role),
    )
    db.commit()


def unassign_pilot_from_flight(db, flight_id, pilot_id):
    """Remove a pilot from a flight's crew.
    Returns the number of rows deleted (0 = assignment not found)."""
    cursor = db.execute(
        "DELETE FROM flight_crew WHERE flight_id = ? AND pilot_id = ?",
        (flight_id, pilot_id),
    )
    db.commit()
    return cursor.rowcount


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

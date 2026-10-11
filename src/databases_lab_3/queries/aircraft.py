"""Aircraft queries."""


def get_aircraft(db, registration=None, status=None):
    """Return aircraft, optionally filtered by registration and/or status."""
    query = """
        SELECT aircraft_id, registration_number, model, manufacturer,
               capacity, range_km, min_runway_m, year_manufactured, status
        FROM aircraft
    """
    conditions = []
    params = []
    if registration is not None:
        conditions.append("registration_number = ?")
        params.append(registration.upper())
    if status is not None:
        conditions.append("LOWER(status) = LOWER(?)")
        params.append(status)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY registration_number"
    return db.execute(query, params).fetchall()


def get_aircraft_by_registration(db, registration):
    """Return an aircraft row matching the registration number, or None."""
    return db.execute(
        "SELECT aircraft_id, registration_number, model FROM aircraft "
        "WHERE registration_number = ?",
        (registration.upper(),),
    ).fetchone()


def add_aircraft(
    db,
    registration_number,
    model,
    manufacturer,
    capacity,
    range_km,
    min_runway_m,
    year_manufactured,
):
    """Insert a new aircraft and return its aircraft_id."""
    cursor = db.execute(
        """
        INSERT INTO aircraft
            (registration_number, model, manufacturer, capacity,
             range_km, min_runway_m, year_manufactured)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            registration_number,
            model,
            manufacturer,
            capacity,
            range_km,
            min_runway_m,
            year_manufactured,
        ),
    )
    db.commit()
    return cursor.lastrowid


def update_aircraft(
    db,
    aircraft_id,
    model=None,
    manufacturer=None,
    capacity=None,
    range_km=None,
    min_runway_m=None,
    year_manufactured=None,
    status=None,
):
    """Update editable fields on an aircraft. Only non-None values are applied."""
    fields = []
    params = []
    for col, val in [
        ("model", model),
        ("manufacturer", manufacturer),
        ("capacity", capacity),
        ("range_km", range_km),
        ("min_runway_m", min_runway_m),
        ("year_manufactured", year_manufactured),
        ("status", status),
    ]:
        if val is not None:
            fields.append(f"{col} = ?")
            params.append(val)
    if not fields:
        return 0
    params.append(aircraft_id)
    cursor = db.execute(
        f"UPDATE aircraft SET {', '.join(fields)} WHERE aircraft_id = ?", params
    )
    db.commit()
    return cursor.rowcount


def delete_aircraft(db, aircraft_id):
    """Delete an aircraft. Returns rowcount (0 if not found).
    Will raise an IntegrityError if the aircraft is assigned to a flight."""
    cursor = db.execute("DELETE FROM aircraft WHERE aircraft_id = ?", (aircraft_id,))
    db.commit()
    return cursor.rowcount

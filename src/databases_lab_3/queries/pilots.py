"""Pilot queries."""


def _placeholders(values):
    return ", ".join("?" * len(values))


def get_pilots(db, licence, name):
    """Return all pilots, with their phone numbers joined into one string.
    Filter by licence number, full name, first name or last name."""
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


def get_pilot_schedule(db, licence_number):
    """Return a pilot's schedule from a given licence number."""
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
    return db.execute(query, (licence_number,)).fetchall()


def get_pilot_by_licence(db, licence_number):
    """Return a pilot row for the given licence number, or None."""
    return db.execute(
        "SELECT pilot_id, first_name, last_name FROM pilot WHERE licence_number = ?",
        (licence_number,),
    ).fetchone()


def add_pilot(db, licence_number, first_name, last_name, hire_date, email):
    """Insert a new pilot and return their pilot_id."""
    cursor = db.execute(
        """
        INSERT INTO pilot (licence_number, first_name, last_name, hire_date, email)
        VALUES (?, ?, ?, ?, ?)
        """,
        (licence_number, first_name, last_name, hire_date, email),
    )
    db.commit()
    return cursor.lastrowid


def update_pilot(
    db, pilot_id, first_name=None, last_name=None, hire_date=None, email=None
):
    """Update editable fields on a pilot. Only non-None values are applied."""
    fields = []
    params = []
    for col, val in [
        ("first_name", first_name),
        ("last_name", last_name),
        ("hire_date", hire_date),
        ("email", email),
    ]:
        if val is not None:
            fields.append(f"{col} = ?")
            params.append(val)
    if not fields:
        return 0
    params.append(pilot_id)
    cursor = db.execute(
        f"UPDATE pilot SET {', '.join(fields)} WHERE pilot_id = ?", params
    )
    db.commit()
    return cursor.rowcount


def delete_pilot(db, pilot_id):
    """Delete a pilot. Raises IntegrityError if assigned to any flight."""
    cursor = db.execute("DELETE FROM pilot WHERE pilot_id = ?", (pilot_id,))
    db.commit()
    return cursor.rowcount


def add_pilot_phone(db, pilot_id, phone_number):
    """Add a phone number to a pilot."""
    db.execute(
        "INSERT INTO pilot_phone (pilot_id, phone_number) VALUES (?, ?)",
        (pilot_id, phone_number),
    )
    db.commit()


def delete_pilot_phone(db, pilot_id, phone_number):
    """Remove a phone number from a pilot. Returns rowcount."""
    cursor = db.execute(
        "DELETE FROM pilot_phone WHERE pilot_id = ? AND phone_number = ?",
        (pilot_id, phone_number),
    )
    db.commit()
    return cursor.rowcount

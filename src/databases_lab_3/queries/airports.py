"""Airport and runway queries."""


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


def get_airport_by_code(db, code):
    """Return a single airport row matching an IATA or ICAO code, or None."""
    return db.execute(
        "SELECT airport_id, iata_code, icao_code, latitude, longitude "
        "FROM airport WHERE iata_code = ? OR icao_code = ?",
        (code.upper(), code.upper()),
    ).fetchone()


def add_airport(
    db,
    iata_code,
    icao_code,
    airport_name,
    city_name,
    country_code,
    timezone,
    latitude,
    longitude,
    elevation_feet,
):
    """Insert a new airport and return its airport_id."""
    cursor = db.execute(
        """
        INSERT INTO airport
            (iata_code, icao_code, airport_name, city_name, country_code,
             timezone, latitude, longitude, elevation_feet)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            iata_code,
            icao_code,
            airport_name,
            city_name,
            country_code,
            timezone,
            latitude,
            longitude,
            elevation_feet,
        ),
    )
    db.commit()
    return cursor.lastrowid


def update_airport(
    db,
    airport_id,
    airport_name=None,
    city_name=None,
    country_code=None,
    timezone=None,
    latitude=None,
    longitude=None,
    elevation_feet=None,
):
    """Update editable fields on an airport. Only non-None values are applied."""
    fields = []
    params = []
    for col, val in [
        ("airport_name", airport_name),
        ("city_name", city_name),
        ("country_code", country_code),
        ("timezone", timezone),
        ("latitude", latitude),
        ("longitude", longitude),
        ("elevation_feet", elevation_feet),
    ]:
        if val is not None:
            fields.append(f"{col} = ?")
            params.append(val)
    if not fields:
        return 0
    params.append(airport_id)
    cursor = db.execute(
        f"UPDATE airport SET {', '.join(fields)} WHERE airport_id = ?", params
    )
    db.commit()
    return cursor.rowcount


def delete_airport(db, airport_id):
    """Delete an airport only if no flight uses it.
    Returns rowcount (0 = not found or in use)."""
    cursor = db.execute(
        """
        DELETE FROM airport
        WHERE airport_id = ?
          AND NOT EXISTS (
              SELECT 1 FROM flight
              WHERE departure_airport_id = airport_id
                 OR arrival_airport_id   = airport_id
          )
        """,
        (airport_id,),
    )
    db.commit()
    return cursor.rowcount


def get_runway(db, airport_id, runway_designation):
    """Return a runway row, or None."""
    return db.execute(
        "SELECT * FROM runway WHERE airport_id = ? AND runway_designation = ?",
        (airport_id, runway_designation),
    ).fetchone()


def add_runway(db, airport_id, runway_designation, length_m, surface):
    """Insert a runway for the given airport."""
    db.execute(
        "INSERT INTO runway (airport_id, runway_designation, length_m, surface) "
        "VALUES (?, ?, ?, ?)",
        (airport_id, runway_designation, length_m, surface),
    )
    db.commit()


def update_runway(db, airport_id, runway_designation, length_m=None, surface=None):
    """Update a runway's length and/or surface."""
    fields = []
    params = []
    if length_m is not None:
        fields.append("length_m = ?")
        params.append(length_m)
    if surface is not None:
        fields.append("surface = ?")
        params.append(surface)
    if not fields:
        return 0
    params += [airport_id, runway_designation]
    cursor = db.execute(
        f"UPDATE runway SET {', '.join(fields)} "
        "WHERE airport_id = ? AND runway_designation = ?",
        params,
    )
    db.commit()
    return cursor.rowcount

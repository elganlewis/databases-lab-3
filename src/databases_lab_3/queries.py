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
        SELECT flight_number, departure_code, arrival_code,
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
        SELECT fd.flight_number, fd.departure_code, fd.arrival_code,
            fd.departure_time, fd.arrival_time, fc.role, fd.status
        FROM pilot p
        JOIN flight_crew fc    ON fc.pilot_id  = p.pilot_id
        JOIN flight_details fd ON fd.flight_id = fc.flight_id
        WHERE p.licence_number = ?
        ORDER BY fd.departure_time;
    """

    params = [licence_number]

    return db.execute(query, params).fetchall()


def get_pilots(db):
    """Return all pilots, with their phone numbers joined into one string."""
    query = """
        SELECT p.licence_number, p.first_name, p.last_name, p.hire_date, p.email,
               GROUP_CONCAT(pp.phone_number, ', ') AS phone_numbers
        FROM pilot p
        LEFT JOIN pilot_phone pp ON pp.pilot_id = p.pilot_id
        GROUP BY p.pilot_id
        ORDER BY p.last_name, p.first_name
    """
    return db.execute(query).fetchall()


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

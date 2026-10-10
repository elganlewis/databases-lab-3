"""SQL queries. Each function takes an open connection and returns rows."""


def get_flights(db, airport=None, status=None):
    """Return flights, optionally filtered by airport code and/or status."""
    query = """
        SELECT flight_number, departure_code, arrival_code,
               departure_time, flight_time_minutes, status
        FROM flight_details
    """
    conditions = []
    params = []
    if airport is not None:
        conditions.append("(departure_code = ? OR arrival_code = ?)")
        params += [airport.upper(), airport.upper()]
    if status is not None:
        conditions.append("LOWER(status) = LOWER(?)")
        params.append(status)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY departure_time"

    return db.execute(query, params).fetchall()

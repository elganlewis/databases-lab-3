-- Flight Management Database - Queries
-- Run after flight_db_create_tables.sql and flight_db_sample_data.sql:
--   sqlite3 flight_management.db < flight_db_queries.sql
--
-- Notes:
--  * Each query uses example values (e.g. 'LHR', flight_id 8) so it runs as written.
--    In the Python application, replace each literal with a ? placeholder and pass the
--    value as a parameter, e.g. db.execute("... WHERE arrival_code = ?", (code,)).
--  * Times are UTC. arrival_time is derived (departure_time + flight_time_minutes)
--    and is available through the flight_details view.
--  * Sections 2, 3 and 4 contain INSERT / UPDATE / DELETE statements that change the data.
--    Re-run flight_db_sample_data.sql to reset it.

PRAGMA foreign_keys = ON;


-- =========================================================
-- 1. FLIGHT RETRIEVAL
-- =========================================================

-- 1.1 All flights, earliest first
SELECT flight_number, departure_code, arrival_code, departure_time, arrival_time,
       flight_time_minutes, status, registration_number AS aircraft_registration
FROM flight_details
ORDER BY departure_time;

-- 1.2 By destination (arrival airport code)
SELECT flight_number, departure_code, arrival_code, departure_time, status
FROM flight_details
WHERE arrival_code = 'LHR'
ORDER BY departure_time;

-- 1.3 By destination city (the view only holds codes, so join the airport table)
SELECT f.flight_number,
       COALESCE(dep.iata_code, dep.icao_code) AS from_code,
       arr.city_name                          AS to_city,
       f.departure_time,
       f.status
FROM flight f
JOIN airport dep ON f.departure_airport_id = dep.airport_id
JOIN airport arr ON f.arrival_airport_id   = arr.airport_id
WHERE arr.city_name = 'Dublin'
ORDER BY f.departure_time;

-- 1.4 By departure airport
SELECT flight_number, departure_code, arrival_code, departure_time, status
FROM flight_details
WHERE departure_code = 'LHR'
ORDER BY departure_time;

-- 1.5 By status
SELECT flight_number, departure_code, arrival_code, departure_time, status
FROM flight_details
WHERE status = 'Delayed'
ORDER BY departure_time;

-- 1.6 By departure date (UTC date)
SELECT flight_number, departure_code, arrival_code, departure_time, status
FROM flight_details
WHERE date(departure_time) = '2026-10-16';

-- 1.7 By departure date range
SELECT flight_number, departure_code, arrival_code, departure_time, status
FROM flight_details
WHERE date(departure_time) BETWEEN '2026-10-01' AND '2026-10-31'
ORDER BY departure_time;

-- 1.8 Multiple criteria: destination + status + date range
SELECT flight_number, departure_code, arrival_code, departure_time, status
FROM flight_details
WHERE arrival_code = 'LHR'
  AND status = 'Scheduled'
  AND date(departure_time) BETWEEN '2026-10-01' AND '2026-10-31'
ORDER BY departure_time;

-- 1.9 Look up by flight number (the same number can run on several dates)
SELECT flight_id, flight_number, departure_code, arrival_code,
       departure_time, arrival_time, status
FROM flight_details
WHERE flight_number = 'BA214';

-- 1.10 Full details for one flight, including its crew
SELECT fd.flight_number, fd.departure_code, fd.arrival_code, fd.departure_time,
       fd.arrival_time, fd.status, fd.registration_number,
       p.first_name || ' ' || p.last_name AS pilot, fc.role
FROM flight_details fd
LEFT JOIN flight_crew fc ON fc.flight_id = fd.flight_id
LEFT JOIN pilot p        ON p.pilot_id   = fc.pilot_id
WHERE fd.flight_id = 1
ORDER BY fc.role;

-- 1.11 Full pilot details, were captain or first officer is null
SELECT fd.flight_id, fd.flight_number, fd.departure_code, fd.arrival_code, fd.departure_time,
       fd.arrival_time, fd.flight_time_minutes, fd.status, fd.registration_number,
       MAX(CASE WHEN fc.role = 'Captain'       THEN p.first_name || ' ' || p.last_name END) AS captain,
       MAX(CASE WHEN fc.role = 'Captain'       THEN p.licence_number END) AS captain_licence_number,
       MAX(CASE WHEN fc.role = 'First Officer' THEN p.first_name || ' ' || p.last_name END) AS first_officer,
       MAX(CASE WHEN fc.role = 'First Officer' THEN p.licence_number END) AS first_officer_licence_number
FROM flight_details fd
LEFT JOIN flight_crew fc ON fc.flight_id = fd.flight_id
LEFT JOIN pilot p        ON p.pilot_id   = fc.pilot_id
GROUP BY fd.flight_id
HAVING first_officer IS NULL OR captain IS NULL;


-- =========================================================
-- 2. SCHEDULE MODIFICATION
-- =========================================================

-- 2.1 Change a flight's departure time (arrival follows automatically, as it is derived)
UPDATE flight
SET departure_time = '2026-10-12 11:00:00'
WHERE flight_id = 7;

-- 2.2 Change a flight's duration
UPDATE flight
SET flight_time_minutes = 80
WHERE flight_id = 8;

-- 2.3 Delay a flight by 90 minutes and mark it Delayed
UPDATE flight
SET departure_time = datetime(departure_time, '+90 minutes'),
    status         = 'Delayed'
WHERE flight_id = 11
  AND status IN ('Scheduled', 'Delayed');

-- 2.4 Cancel a flight (only if it has not departed or completed)
UPDATE flight
SET status = 'Cancelled'
WHERE flight_id = 15
  AND status IN ('Scheduled', 'Delayed');

-- 2.5 Change the aircraft assigned to a flight
UPDATE flight
SET aircraft_id = 3
WHERE flight_id = 7;

-- 2.6 Check the changes
SELECT flight_id, flight_number, departure_time, arrival_time,
       flight_time_minutes, status, registration_number
FROM flight_details
WHERE flight_id IN (7, 8, 11, 15)
ORDER BY flight_id;

-- 2.7 Status refresh: flights that have departed but not yet landed become In Progress
UPDATE flight
SET status = 'In Progress'
WHERE status IN ('Scheduled', 'Delayed')
  AND departure_time <= datetime('now')
  AND datetime(departure_time, '+' || flight_time_minutes || ' minutes') > datetime('now');

-- 2.8 Status refresh: flights that have landed become Completed
UPDATE flight
SET status = 'Completed'
WHERE status IN ('Scheduled', 'Delayed', 'In Progress')
  AND datetime(departure_time, '+' || flight_time_minutes || ' minutes') <= datetime('now');


-- =========================================================
-- 3. PILOT ASSIGNMENT
-- =========================================================

-- 3.1 Which pilots are free for flight 8? (not on any overlapping flight)
SELECT p.pilot_id, p.first_name, p.last_name, p.licence_number
FROM pilot p
WHERE p.pilot_id NOT IN (
    SELECT fc.pilot_id
    FROM flight_crew fc
    JOIN flight_details fd     ON fd.flight_id = fc.flight_id
    JOIN flight_details target ON target.flight_id = 8
    WHERE fd.departure_time < target.arrival_time
      AND fd.arrival_time   > target.departure_time
)
ORDER BY p.last_name;

-- 3.2 Conflict check before assigning pilot 2 to flight 8 (no rows = no clash)
SELECT fd.flight_number, fd.departure_time, fd.arrival_time
FROM flight_crew fc
JOIN flight_details fd     ON fd.flight_id = fc.flight_id
JOIN flight_details target ON target.flight_id = 8
WHERE fc.pilot_id = 2
  AND fd.flight_id <> target.flight_id
  AND fd.departure_time < target.arrival_time
  AND fd.arrival_time   > target.departure_time;

-- 3.3 Does flight 8 already have a Captain? (0 = no, safe to add one)
SELECT COUNT(*) AS captains
FROM flight_crew
WHERE flight_id = 8 AND role = 'Captain';

-- 3.4 Assign pilots to a flight
INSERT INTO flight_crew (flight_id, pilot_id, role) VALUES (8, 2,  'Captain');
INSERT INTO flight_crew (flight_id, pilot_id, role) VALUES (8, 11, 'First Officer');

-- 3.5 Change a pilot's role on a flight
UPDATE flight_crew
SET role = 'First Officer'
WHERE flight_id = 8 AND pilot_id = 11;

-- 3.6 Remove a pilot from a flight
DELETE FROM flight_crew
WHERE flight_id = 8 AND pilot_id = 11;

-- 3.7 Crew for a flight
SELECT p.pilot_id, p.first_name, p.last_name, fc.role
FROM flight_crew fc
JOIN pilot p ON p.pilot_id = fc.pilot_id
WHERE fc.flight_id = 8
ORDER BY fc.role;

-- 3.8 A pilot's full schedule (by licence number)
SELECT fd.flight_number, fd.departure_code, fd.arrival_code,
       fd.departure_time, fd.arrival_time, fc.role, fd.status
FROM pilot p
JOIN flight_crew fc    ON fc.pilot_id  = p.pilot_id
JOIN flight_details fd ON fd.flight_id = fc.flight_id
WHERE p.licence_number = 'UK-10234'
ORDER BY fd.departure_time;

-- 3.9 A pilot's upcoming flights only (UTC)
SELECT fd.flight_number, fd.departure_code, fd.arrival_code,
       fd.departure_time, fc.role, fd.status
FROM pilot p
JOIN flight_crew fc    ON fc.pilot_id  = p.pilot_id
JOIN flight_details fd ON fd.flight_id = fc.flight_id
WHERE p.pilot_id = 3
  AND fd.departure_time > datetime('now')
  AND fd.status <> 'Cancelled'
ORDER BY fd.departure_time;

-- 3.10 Upcoming flights that do not yet have a full crew (fewer than 2 pilots)
SELECT fd.flight_number, fd.departure_code, fd.arrival_code, fd.departure_time,
       fd.status, COUNT(fc.pilot_id) AS pilots_assigned
FROM flight_details fd
LEFT JOIN flight_crew fc ON fc.flight_id = fd.flight_id
WHERE fd.status IN ('Scheduled', 'Delayed')
GROUP BY fd.flight_id
HAVING COUNT(fc.pilot_id) < 2
ORDER BY fd.departure_time;


-- =========================================================
-- 4. DESTINATION (AIRPORT) MANAGEMENT
-- =========================================================

-- 4.1 View all airports
SELECT a.airport_id, a.iata_code, a.icao_code, a.airport_name, a.city_name, a.country_code,
       a.timezone, a.latitude, a.longitude, a.elevation_feet, group_concat(r.runway_designation || ' (' || r.length_m || ' m)', ', ') AS runways
FROM airport a 
LEFT JOIN runway r ON r.airport_id = a.airport_id
GROUP BY a.airport_id
ORDER BY country_code, city_name;

-- 4.2 Search by city or country code
SELECT iata_code, airport_name, city_name, country_code
FROM airport
WHERE city_name = 'London' OR country_code = 'GB'
ORDER BY city_name;

-- 4.3 One airport with its runways listed on a single line
SELECT a.iata_code, a.airport_name, a.city_name, a.elevation_feet,
       group_concat(r.runway_designation || ' (' || r.length_m || ' m)', ', ') AS runways
FROM airport a
LEFT JOIN runway r ON r.airport_id = a.airport_id
WHERE a.iata_code = 'LHR'
GROUP BY a.airport_id;

-- 4.4 Add a new airport and a runway for it
INSERT INTO airport (iata_code, icao_code, airport_name, city_name, country_code,
                     timezone, latitude, longitude, elevation_feet)
VALUES ('EDI', 'EGPH', 'Edinburgh Airport', 'Edinburgh', 'GB',
        'Europe/London', 55.950000, -3.372500, 135);

INSERT INTO runway (airport_id, runway_designation, length_m, surface)
SELECT airport_id, '06', 2556, 'Asphalt' FROM airport WHERE iata_code = 'EDI';

-- 4.5 Update airport information
UPDATE airport
SET airport_name = 'Edinburgh International Airport',
    elevation_feet = 136
WHERE iata_code = 'EDI';

-- 4.6 Update a runway (e.g. after an extension or resurfacing)
UPDATE runway
SET length_m = 2600, surface = 'Asphalt/Concrete'
WHERE runway_designation = '06'
  AND airport_id = (SELECT airport_id FROM airport WHERE iata_code = 'EDI');

-- 4.7 Check the changes
SELECT a.iata_code, a.airport_name, a.elevation_feet, r.runway_designation, r.length_m, r.surface
FROM airport a
LEFT JOIN runway r ON r.airport_id = a.airport_id
WHERE a.iata_code = 'EDI';

-- 4.8 Delete a runway
DELETE FROM runway
WHERE runway_designation = '06'
  AND airport_id = (SELECT airport_id FROM airport WHERE iata_code = 'EDI');

-- 4.9 Delete an airport only if no flight uses it (its runways are deleted with it)
DELETE FROM airport
WHERE iata_code = 'EDI'
  AND NOT EXISTS (SELECT 1 FROM flight
                  WHERE departure_airport_id = airport.airport_id
                     OR arrival_airport_id   = airport.airport_id);

-- 4.10 Which airports can an aircraft use? (needs a runway at least min_runway_m long)
SELECT a.iata_code, a.airport_name, MAX(r.length_m) AS longest_runway_m
FROM airport a
JOIN runway r ON r.airport_id = a.airport_id
GROUP BY a.airport_id
HAVING MAX(r.length_m) >= (SELECT min_runway_m FROM aircraft WHERE registration_number = 'G-XWBA')
ORDER BY a.iata_code;


-- =========================================================
-- 5. SUMMARY QUERIES
-- =========================================================

-- 5.1 Number of flights to each destination (airports with none are included)
SELECT a.iata_code, a.airport_name, COUNT(f.flight_id) AS flights_arriving
FROM airport a
LEFT JOIN flight f ON f.arrival_airport_id = a.airport_id
GROUP BY a.airport_id
ORDER BY flights_arriving DESC, a.airport_name;

-- 5.2 Same, ignoring cancelled flights
SELECT a.iata_code, a.airport_name, COUNT(f.flight_id) AS flights_arriving
FROM airport a
LEFT JOIN flight f ON f.arrival_airport_id = a.airport_id
                  AND f.status <> 'Cancelled'
GROUP BY a.airport_id
ORDER BY flights_arriving DESC, a.airport_name;

-- 5.3 Number of flights departing from each airport
SELECT a.iata_code, a.airport_name, COUNT(f.flight_id) AS flights_departing
FROM airport a
LEFT JOIN flight f ON f.departure_airport_id = a.airport_id
GROUP BY a.airport_id
ORDER BY flights_departing DESC, a.airport_name;

-- 5.4 Number of flights by status
SELECT status, COUNT(*) AS flights
FROM flight
GROUP BY status
ORDER BY flights DESC;

-- 5.5 Number of flights assigned to each pilot, split by role (pilots with none are included)
SELECT p.pilot_id,
       p.first_name || ' ' || p.last_name AS pilot,
       COUNT(fc.flight_id) AS flights_assigned,
       COALESCE(SUM(CASE WHEN fc.role = 'Captain'       THEN 1 ELSE 0 END), 0) AS as_captain,
       COALESCE(SUM(CASE WHEN fc.role = 'First Officer' THEN 1 ELSE 0 END), 0) AS as_first_officer
FROM pilot p
LEFT JOIN flight_crew fc ON fc.pilot_id = p.pilot_id
GROUP BY p.pilot_id
ORDER BY flights_assigned DESC, p.last_name;

-- 5.6 Hours flown by each pilot on completed flights
SELECT p.pilot_id,
       p.first_name || ' ' || p.last_name AS pilot,
       COUNT(f.flight_id) AS completed_flights,
       ROUND(COALESCE(SUM(f.flight_time_minutes), 0) / 60.0, 1) AS hours_flown
FROM pilot p
LEFT JOIN flight_crew fc ON fc.pilot_id = p.pilot_id
LEFT JOIN flight f       ON f.flight_id = fc.flight_id AND f.status = 'Completed'
GROUP BY p.pilot_id
ORDER BY hours_flown DESC, p.last_name;

-- 5.7 Busiest routes
SELECT departure_code || ' -> ' || arrival_code AS route,
       COUNT(*) AS flights,
       ROUND(AVG(flight_time_minutes)) AS avg_minutes
FROM flight_details
GROUP BY departure_code, arrival_code
ORDER BY flights DESC, route;

-- 5.8 Flights and hours per aircraft
SELECT ac.registration_number, ac.model, ac.status,
       COUNT(f.flight_id) AS flights,
       ROUND(COALESCE(SUM(f.flight_time_minutes), 0) / 60.0, 1) AS scheduled_hours
FROM aircraft ac
LEFT JOIN flight f ON f.aircraft_id = ac.aircraft_id AND f.status <> 'Cancelled'
GROUP BY ac.aircraft_id
ORDER BY flights DESC, ac.registration_number;

-- 5.9 Flights per month
SELECT strftime('%Y-%m', departure_time) AS month, COUNT(*) AS flights
FROM flight
GROUP BY month
ORDER BY month;

-- 5.10 Number of runways and longest runway at each airport
SELECT a.iata_code, a.airport_name,
       COUNT(r.runway_designation) AS runways,
       MAX(r.length_m)             AS longest_runway_m
FROM airport a
LEFT JOIN runway r ON r.airport_id = a.airport_id
GROUP BY a.airport_id
ORDER BY longest_runway_m DESC;
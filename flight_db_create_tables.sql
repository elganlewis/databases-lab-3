-- Flight Management Database
-- Run with:  sqlite3 flight_management.db < flight_db_create_tables.sql

-- Relational Schema:

-- Airport(airport_id PK, iata_code, icao_code, airport_name, city_name, country_code, timezone, latitude, longitude)
-- Aircraft(aircraft_id PK, model, manufacturer, capacity, registration_number, range_km, min_runway_m, year_manufactured, status)
-- Flight(flight_id PK, flight_number, departure_airport_id FK, arrival_airport_id FK, aircraft_id FK, departure_time, arrival_time, status)
-- Pilot(pilot_id PK, licence_number, first_name, last_name, hire_date, email)
-- Flight_Crew(flight_id PK/FK, pilot_id PK/FK, role)
-- Runway(airport_id PK/FK, runway_designation PK, length_m, surface)
-- Pilot_Phone(pilot_id PK/FK, phone_number PK)

-- Date/time format: dates are 'YYYY-MM-DD', date-times are 'YYYY-MM-DD HH:MM:SS'.
-- All flight times are stored in UTC; airport.timezone is used to convert for display.

-- Foreign keys are OFF by default in SQLite, so turn them on (every connection).
PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS flight_details;
DROP TABLE IF EXISTS flight_crew;
DROP TABLE IF EXISTS pilot_phone;
DROP TABLE IF EXISTS flight;
DROP TABLE IF EXISTS runway;
DROP TABLE IF EXISTS pilot;
DROP TABLE IF EXISTS aircraft;
DROP TABLE IF EXISTS airport;

-- ---------------------------------------------------------
-- AIRPORT
-- ---------------------------------------------------------
CREATE TABLE airport (
    airport_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    iata_code     CHAR(3) UNIQUE CHECK (iata_code IS NULL OR length(iata_code) = 3),
    icao_code     CHAR(4) NOT NULL UNIQUE CHECK (length(icao_code) = 4),
    airport_name  VARCHAR(100) NOT NULL,
    city_name     VARCHAR(100) NOT NULL,
    country_code  CHAR(2) NOT NULL CHECK (length(country_code) = 2), -- ISO 3166-1 alpha-2
    timezone      VARCHAR(50) NOT NULL,                              -- IANA name, e.g. Europe/London
    latitude      DECIMAL(9,6) NOT NULL CHECK (latitude  BETWEEN -90  AND 90),
    longitude     DECIMAL(9,6) NOT NULL CHECK (longitude BETWEEN -180 AND 180)
);

-- ---------------------------------------------------------
-- RUNWAY (weak entity, identified by airport_id + runway_designation)
-- ---------------------------------------------------------
CREATE TABLE runway (
    airport_id          INTEGER NOT NULL,
    runway_designation  VARCHAR(3) NOT NULL,
    length_m            INTEGER NOT NULL CHECK (length_m > 0),
    surface             VARCHAR(20) NOT NULL,

    PRIMARY KEY (airport_id, runway_designation),
    FOREIGN KEY (airport_id) REFERENCES airport(airport_id) ON DELETE CASCADE
);

-- ---------------------------------------------------------
-- AIRCRAFT
-- ---------------------------------------------------------
CREATE TABLE aircraft (
    aircraft_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_number VARCHAR(10) NOT NULL UNIQUE,
    model               VARCHAR(50) NOT NULL,
    manufacturer        VARCHAR(50) NOT NULL,
    capacity            INTEGER NOT NULL CHECK (capacity > 0),
    range_km            INTEGER NOT NULL CHECK (range_km > 0),
    min_runway_m        INTEGER NOT NULL CHECK (min_runway_m > 0),  -- shortest runway it can use
    year_manufactured   INTEGER NOT NULL CHECK (year_manufactured BETWEEN 1950 AND 2100),
    status              VARCHAR(20) NOT NULL DEFAULT 'Active'
                        CHECK (status IN ('Active', 'In Maintenance', 'Retired'))
);

-- ---------------------------------------------------------
-- PILOT
-- ---------------------------------------------------------
CREATE TABLE pilot (
    pilot_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    licence_number VARCHAR(50) NOT NULL UNIQUE,
    first_name     VARCHAR(100) NOT NULL,
    last_name      VARCHAR(100) NOT NULL,
    hire_date      DATE CHECK (hire_date IS NULL OR date(hire_date) IS hire_date),  -- 'YYYY-MM-DD'
    email          VARCHAR(100) UNIQUE
);

-- ---------------------------------------------------------
-- PILOT_PHONE (multi-valued attribute: phone_number)
-- ---------------------------------------------------------
CREATE TABLE pilot_phone (
    pilot_id     INTEGER NOT NULL,
    phone_number VARCHAR(20) NOT NULL,

    PRIMARY KEY (pilot_id, phone_number),
    FOREIGN KEY (pilot_id) REFERENCES pilot(pilot_id) ON DELETE CASCADE
);

-- ---------------------------------------------------------
-- FLIGHT
-- Times are stored as text in 'YYYY-MM-DD HH:MM:SS' format (UTC).
-- The datetime(x) IS x checks reject any other format.
-- ---------------------------------------------------------
CREATE TABLE flight (
    flight_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_number        VARCHAR(10) NOT NULL,
    departure_airport_id INTEGER NOT NULL,
    arrival_airport_id   INTEGER NOT NULL,
    aircraft_id          INTEGER NOT NULL,
    departure_time       DATETIME NOT NULL CHECK (datetime(departure_time) IS departure_time),
    arrival_time         DATETIME NOT NULL CHECK (datetime(arrival_time)   IS arrival_time),
    status               VARCHAR(20) NOT NULL DEFAULT 'Scheduled'
                         CHECK (status IN ('Scheduled', 'In Progress', 'Delayed', 'Cancelled', 'Completed')),

    FOREIGN KEY (departure_airport_id) REFERENCES airport(airport_id)   ON DELETE RESTRICT,
    FOREIGN KEY (arrival_airport_id)   REFERENCES airport(airport_id)   ON DELETE RESTRICT,
    FOREIGN KEY (aircraft_id)          REFERENCES aircraft(aircraft_id) ON DELETE RESTRICT,

    CHECK (departure_airport_id <> arrival_airport_id),
    CHECK (arrival_time > departure_time),
    UNIQUE (flight_number, departure_time)
);

-- ---------------------------------------------------------
-- FLIGHT_CREW (junction table for Crews)
-- ---------------------------------------------------------
CREATE TABLE flight_crew (
    flight_id INTEGER NOT NULL,
    pilot_id  INTEGER NOT NULL,
    role      VARCHAR(20) NOT NULL CHECK (role IN ('Captain', 'First Officer')),

    PRIMARY KEY (flight_id, pilot_id),
    FOREIGN KEY (flight_id) REFERENCES flight(flight_id) ON DELETE CASCADE,
    FOREIGN KEY (pilot_id)  REFERENCES pilot(pilot_id)   ON DELETE RESTRICT
);

-- ---------------------------------------------------------
-- VIEW: derived flight_time (in minutes)
-- Shows the IATA code where one exists, otherwise the ICAO code.
-- ---------------------------------------------------------
CREATE VIEW flight_details AS
SELECT f.flight_id,
       f.flight_number,
       COALESCE(dep.iata_code, dep.icao_code) AS departure_code,
       COALESCE(arr.iata_code, arr.icao_code) AS arrival_code,
       f.departure_time,
       f.arrival_time,
       CAST(ROUND((julianday(f.arrival_time) - julianday(f.departure_time)) * 24 * 60)
            AS INTEGER) AS flight_time_minutes,
       f.status,
       a.registration_number
FROM flight f
JOIN airport  dep ON f.departure_airport_id = dep.airport_id
JOIN airport  arr ON f.arrival_airport_id   = arr.airport_id
JOIN aircraft a   ON f.aircraft_id          = a.aircraft_id;

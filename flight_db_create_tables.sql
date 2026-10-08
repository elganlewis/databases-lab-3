-- Flight Management Database (SQLite 3 syntax)
-- Run with:  sqlite3 flight_management.db < flight_management_sqlite.sql

-- Relational Schema:

-- Airport(airport_id PK, iata_code, icao_code, airport_name, city_name, country_code, timezone, latitude, longitude)
-- Aircraft(aircraft_id PK, model, manufacturer, capacity, registration_number, range_km, year_manufactured, status)
-- Flight(flight_id PK, flight_number, departure_airport_id FK, arrival_airport_id FK, aircraft_id FK, departure_time, arrival_time, status)
-- Pilot(pilot_id PK, licence_number, first_name, last_name, hire_date, email)
-- Flight_Crew(flight_id PK/FK, pilot_id PK/FK, role)
-- Runway(airport_id PK/FK, runway_designation PK, length_m, surface)
-- Pilot_Phone(pilot_id PK/FK, phone_number PK)

-- Foreign keys are OFF by default in SQLite so need to turn on.
PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS flight_details;
DROP TABLE IF EXISTS flight_crew;
DROP TABLE IF EXISTS flight;
DROP TABLE IF EXISTS pilot;
DROP TABLE IF EXISTS pilot_phone;
DROP TABLE IF EXISTS runway;
DROP TABLE IF EXISTS aircraft;
DROP TABLE IF EXISTS destination;

-- ---------------------------------------------------------
-- AIRPORT
-- ---------------------------------------------------------
CREATE TABLE airport (
    airport_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    iata_code           CHAR(3) UNIQUE CHECK (iata_code IS NULL OR length(iata_code) = 3),
    icao_code           CHAR(4) NOT NULL UNIQUE CHECK (length(icao_code) = 4),
    airport_name        VARCHAR(100) NOT NULL,
    city_name           VARCHAR(100) NOT NULL,
    timezone            TEXT NOT NULL,
    country_code        TEXT NOT NULL CHECK (length(country_code) = 2), -- ISO 3166-1 alpha-2
    latitude            TEXT NOT NULL,
    longitude           TEXT NOT NULL
);

-- ---------------------------------------------------------
-- RUNWAY
-- ---------------------------------------------------------
CREATE TABLE runway (
    airport_id          INTEGER NOT NULL,
    runway_designation  VARCHAR(3),
    length_m            INTEGER NOT NULL,
    surface             VARCHAR(20) NOT NULL,

    PRIMARY KEY (airport_id, runway_designation),
    FOREIGN KEY (airport_id) REFERENCES airport(airport_id) ON DELETE CASCADE,
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
    year_manufactured   CHAR(4) NOT NULL,
    status 
);

-- ---------------------------------------------------------
-- PILOT
-- ---------------------------------------------------------
CREATE TABLE pilot (
    pilot_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    licence_number VARCHAR(50) NOT NULL UNIQUE,
    first_name     VARCHAR(100) NOT NULL,
    last_name      VARCHAR(100) NOT NULL,
    hire_date      CHAR(10),            -- stored as 'YYYY-MM-DD'
    email          VARCHAR(100) UNIQUE
);

-- ---------------------------------------------------------
-- PILOT_PHONE
-- ---------------------------------------------------------
CREATE TABLE pilot_phone (
    pilot_id PK/FK,
    phone_number PK
);

-- ---------------------------------------------------------
-- FLIGHT
-- Times are stored as text in 'YYYY-MM-DD HH:MM:SS' format.
-- ---------------------------------------------------------
CREATE TABLE flight (
    flight_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_number  TEXT NOT NULL,
    departure_time TEXT NOT NULL,
    arrival_time   TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'Scheduled'
                   CHECK (status IN ('Scheduled', 'Delayed', 'Cancelled', 'Completed')),
    departure_airport_id      INTEGER NOT NULL,
    arrival_airport_if INTEGER NOT NULL,
    aircraft_id    INTEGER NOT NULL,

    FOREIGN KEY (departure_airport_id)      REFERENCES airport(airport_id) ON DELETE RESTRICT,
    FOREIGN KEY (arrival_airport_id) REFERENCES airport(airport_id) ON DELETE RESTRICT,
    FOREIGN KEY (aircraft_id)    REFERENCES aircraft(aircraft_id)       ON DELETE RESTRICT,

    CHECK (departure_airport_id <> arrival_airport_if),
    CHECK (arrival_time > departure_time),
    UNIQUE (flight_number, departure_time)
);

-- ---------------------------------------------------------
-- FLIGHT_CREW (junction table for Crews)
-- ---------------------------------------------------------
CREATE TABLE flight_crew (
    flight_id INTEGER NOT NULL,
    pilot_id  INTEGER NOT NULL,
    role      TEXT NOT NULL CHECK (role IN ('Captain', 'First Officer')),

    PRIMARY KEY (flight_id, pilot_id),
    FOREIGN KEY (flight_id) REFERENCES flight(flight_id) ON DELETE CASCADE,
    FOREIGN KEY (pilot_id)  REFERENCES pilot(pilot_id)   ON DELETE RESTRICT
);

-- ---------------------------------------------------------
-- VIEW: derived flight_time (in minutes)
-- ---------------------------------------------------------
CREATE VIEW flight_details AS
SELECT f.flight_id,
       f.flight_number,
       o.airport_code AS origin_code,
       d.airport_code AS destination_code,
       f.departure_time,
       f.arrival_time,
       CAST((julianday(f.arrival_time) - julianday(f.departure_time)) * 24 * 60 AS INTEGER)
           AS flight_time_minutes,
       f.status,
       a.registration_number
FROM flight f
JOIN destination o ON f.origin_id      = o.destination_id
JOIN destination d ON f.destination_id = d.destination_id
JOIN aircraft a    ON f.aircraft_id    = a.aircraft_id;

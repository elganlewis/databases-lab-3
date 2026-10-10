-- Flight Management Database - Sample Data
-- Run AFTER flight_db_create_tables.sql:
--   sqlite3 flight_management.db < flight_db_sample_data.sql
--
-- Notes:
--  * Flight departure times are UTC, format 'YYYY-MM-DD HH:MM:SS'.
--    Each flight stores its duration (flight_time_minutes); arrival_time is
--    derived (departure_time + duration) and is available through the flight_details view.
--  * Sample data was generated with AI assistance. Airport codes, coordinates, elevations
--    and runway lengths are approximate; aircraft specifications and minimum runway
--    figures are simplified. Pilots, registrations, contact details and flights are fictional.
--  * Statuses are consistent with a "current date" of early October 2026:
--    Completed flights are in the past, all other statuses are in the future.
--  * Every flight's aircraft is Active, within range of its route, and can use the
--    longest runway at both airports.

PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

-- ---------------------------------------------------------
-- Clear existing rows (children first) so this script can be re-run,
-- and reset the AUTOINCREMENT counters.
-- ---------------------------------------------------------
DELETE FROM flight_crew;
DELETE FROM pilot_phone;
DELETE FROM flight;
DELETE FROM runway;
DELETE FROM pilot;
DELETE FROM aircraft;
DELETE FROM airport;
DELETE FROM sqlite_sequence WHERE name IN ('airport', 'aircraft', 'pilot', 'flight');

-- ---------------------------------------------------------
-- AIRPORT (12 rows)
-- ---------------------------------------------------------
INSERT INTO airport (airport_id, iata_code, icao_code, airport_name, city_name, country_code, timezone, latitude, longitude, elevation_feet) VALUES
    ( 1, 'LHR', 'EGLL', 'Heathrow Airport',                      'London',      'GB', 'Europe/London',       51.470000,   -0.454300,   83),
    ( 2, 'CDG', 'LFPG', 'Charles de Gaulle Airport',             'Paris',       'FR', 'Europe/Paris',        49.009700,    2.547900,  392),
    ( 3, 'JFK', 'KJFK', 'John F. Kennedy International Airport', 'New York',    'US', 'America/New_York',    40.641300,  -73.778100,   13),
    ( 4, 'AMS', 'EHAM', 'Amsterdam Airport Schiphol',            'Amsterdam',   'NL', 'Europe/Amsterdam',    52.310500,    4.768300,  -11),
    ( 5, 'FRA', 'EDDF', 'Frankfurt Airport',                     'Frankfurt',   'DE', 'Europe/Berlin',       50.033300,    8.570600,  364),
    ( 6, 'MAD', 'LEMD', 'Adolfo Suarez Madrid-Barajas Airport',  'Madrid',      'ES', 'Europe/Madrid',       40.471900,   -3.562600, 2001),
    ( 7, 'DXB', 'OMDB', 'Dubai International Airport',           'Dubai',       'AE', 'Asia/Dubai',          25.253200,   55.365700,   62),
    ( 8, 'SIN', 'WSSS', 'Singapore Changi Airport',              'Singapore',   'SG', 'Asia/Singapore',       1.359200,  103.989400,   22),
    ( 9, 'LAX', 'KLAX', 'Los Angeles International Airport',     'Los Angeles', 'US', 'America/Los_Angeles', 33.942500, -118.408100,  128),
    (10, 'CWL', 'EGFF', 'Cardiff Airport',                       'Cardiff',     'GB', 'Europe/London',       51.396700,   -3.343300,  220),
    (11, 'MAN', 'EGCC', 'Manchester Airport',                    'Manchester',  'GB', 'Europe/London',       53.353700,   -2.274900,  257),
    (12, 'DUB', 'EIDW', 'Dublin Airport',                        'Dublin',      'IE', 'Europe/Dublin',       53.421300,   -6.270100,  242);

-- ---------------------------------------------------------
-- RUNWAY (15 rows)
-- Cardiff's only runway (2,392 m) is too short for the larger aircraft,
-- which is useful for testing the minimum runway check.
-- ---------------------------------------------------------
INSERT INTO runway (airport_id, runway_designation, length_m, surface) VALUES
    ( 1, '09L', 3902, 'Asphalt'),
    ( 1, '09R', 3660, 'Asphalt'),
    ( 2, '08R', 4215, 'Asphalt'),
    ( 3, '04L', 3460, 'Asphalt'),
    ( 3, '13R', 4423, 'Asphalt'),
    ( 4, '18R', 3800, 'Asphalt'),
    ( 5, '07C', 4000, 'Concrete'),
    ( 6, '14L', 4350, 'Asphalt'),
    ( 7, '12L', 4447, 'Asphalt'),
    ( 8, '02L', 4000, 'Asphalt'),
    ( 9, '07L', 3685, 'Concrete'),
    (10, '12',  2392, 'Asphalt'),
    (11, '05L', 3048, 'Asphalt'),
    (11, '05R', 3050, 'Asphalt'),
    (12, '10R', 3110, 'Asphalt');

-- ---------------------------------------------------------
-- AIRCRAFT (12 rows)
-- Aircraft 9 is In Maintenance and aircraft 10 is Retired, so neither is used on a flight.
-- ---------------------------------------------------------
INSERT INTO aircraft (aircraft_id, registration_number, model, manufacturer, capacity, range_km, min_runway_m, year_manufactured, status) VALUES
    ( 1, 'G-EUPT', 'A320',       'Airbus',  180,  6100, 2100, 2012, 'Active'),
    ( 2, 'G-XWBA', 'A350-1000',  'Airbus',  331, 15000, 2600, 2019, 'Active'),
    ( 3, 'G-FMDA', 'A320',       'Airbus',  180,  6100, 2100, 2015, 'Active'),
    ( 4, 'G-FMDB', 'A321',       'Airbus',  220,  5950, 2200, 2017, 'Active'),
    ( 5, 'G-FMDC', '737-800',    'Boeing',  189,  5400, 2300, 2010, 'Active'),
    ( 6, 'G-FMDD', '787-9',      'Boeing',  290, 14140, 2800, 2018, 'Active'),
    ( 7, 'G-FMDE', '777-300ER',  'Boeing',  350, 13650, 3000, 2016, 'Active'),
    ( 8, 'G-FMDF', 'A220-300',   'Airbus',  145,  6300, 1900, 2021, 'Active'),
    ( 9, 'G-FMDG', 'E190',       'Embraer', 100,  4500, 1800, 2013, 'In Maintenance'),
    (10, 'G-FMDH', 'A319',       'Airbus',  144,  6850, 2000, 2008, 'Retired'),
    (11, 'G-FMDI', 'A330-300',   'Airbus',  300, 11750, 2500, 2011, 'Active'),
    (12, 'G-FMDJ', 'ATR 72-600', 'ATR',      70,  1500, 1300, 2019, 'Active');

-- ---------------------------------------------------------
-- PILOT (12 rows)
-- Captains (1, 2, 3, 5, 7, 10) are the more senior hires.
-- Pilot 12 has no email and no phone number on record (both are optional).
-- ---------------------------------------------------------
INSERT INTO pilot (pilot_id, licence_number, first_name, last_name, hire_date, email) VALUES
    ( 1, 'UK-10234', 'Sarah',   'Evans',     '2009-03-12', 'sarah.evans@example.com'),
    ( 2, 'UK-10987', 'James',   'Morgan',    '2011-07-01', 'james.morgan@example.com'),
    ( 3, 'UK-11456', 'Priya',   'Patel',     '2012-01-20', 'priya.patel@example.com'),
    ( 4, 'UK-12033', 'Owen',    'Davies',    '2018-09-03', 'owen.davies@example.com'),
    ( 5, 'UK-12378', 'Amelia',  'Clarke',    '2010-05-23', 'amelia.clarke@example.com'),
    ( 6, 'UK-12844', 'Daniel',  'Okafor',    '2019-02-11', 'daniel.okafor@example.com'),
    ( 7, 'UK-13102', 'Megan',   'Hughes',    '2013-11-06', 'megan.hughes@example.com'),
    ( 8, 'UK-13559', 'Tomasz',  'Kowalski',  '2017-04-28', 'tomasz.kowalski@example.com'),
    ( 9, 'UK-13971', 'Fatima',  'Al-Sayed',  '2021-08-16', 'fatima.alsayed@example.com'),
    (10, 'UK-14320', 'Liam',    'O''Connor', '2008-01-14', 'liam.oconnor@example.com'),
    (11, 'UK-14687', 'Hannah',  'Williams',  '2022-03-07', 'hannah.williams@example.com'),
    (12, 'UK-15014', 'Rhys',    'Jenkins',   '2023-06-19', NULL);

-- ---------------------------------------------------------
-- PILOT_PHONE (14 rows)
-- Some pilots have two numbers (multi-valued attribute); pilot 12 has none.
-- Numbers are in Ofcom's reserved ranges for drama/fictional use.
-- ---------------------------------------------------------
INSERT INTO pilot_phone (pilot_id, phone_number) VALUES
    ( 1, '07700 900111'),
    ( 1, '01632 960001'),
    ( 2, '07700 900222'),
    ( 3, '07700 900333'),
    ( 4, '07700 900444'),
    ( 4, '029 2018 0123'),
    ( 5, '07700 900555'),
    ( 6, '07700 900666'),
    ( 7, '07700 900777'),
    ( 7, '029 2018 0456'),
    ( 8, '07700 900888'),
    ( 9, '07700 900999'),
    (10, '07700 900101'),
    (11, '07700 900202');

-- ---------------------------------------------------------
-- FLIGHT (15 rows)
-- 1-6 Completed | 7, 9, 11, 12, 13, 15 Scheduled | 8, 10 Delayed | 14 Cancelled
-- Delayed flights show their revised departure times.
-- flight_time_minutes is the stored duration; arrival_time is derived in the view.
-- ---------------------------------------------------------
INSERT INTO flight (flight_id, flight_number, departure_airport_id, arrival_airport_id, aircraft_id, departure_time, flight_time_minutes, status) VALUES
    ( 1, 'BA214',  1,  2,  1, '2026-09-14 08:30:00',  75, 'Completed'),
    ( 2, 'BA330',  1,  3,  2, '2026-09-18 14:00:00', 475, 'Completed'),
    ( 3, 'BA402',  4,  1,  3, '2026-09-21 06:15:00',  75, 'Completed'),
    ( 4, 'BA118',  1,  5,  4, '2026-09-25 11:40:00',  90, 'Completed'),
    ( 5, 'BA761', 11, 12, 12, '2026-09-29 09:00:00',  55, 'Completed'),
    ( 6, 'BA506',  1,  6,  5, '2026-10-03 15:20:00', 155, 'Completed'),
    ( 7, 'BA215',  2,  1,  1, '2026-10-12 10:30:00',  75, 'Scheduled'),
    ( 8, 'BA703',  1,  4,  3, '2026-10-14 09:15:00',  70, 'Delayed'),
    ( 9, 'BA331',  3,  1,  2, '2026-10-16 22:30:00', 410, 'Scheduled'),
    (10, 'BA555',  5,  1,  4, '2026-10-18 18:45:00',  90, 'Delayed'),
    (11, 'BA640',  1,  7,  7, '2026-10-20 21:15:00', 420, 'Scheduled'),
    (12, 'BA871',  7,  8,  6, '2026-10-25 02:30:00', 460, 'Scheduled'),
    (13, 'BA932',  9,  1, 11, '2026-11-02 20:00:00', 630, 'Scheduled'),
    (14, 'BA117', 10, 12, 12, '2026-11-05 07:45:00',  55, 'Cancelled'),
    (15, 'BA226',  1,  8,  2, '2026-11-10 20:40:00', 780, 'Scheduled');

-- ---------------------------------------------------------
-- FLIGHT_CREW (15 rows)
-- Flights 1-7 have a full crew (Captain + First Officer). Flight 9 has a Captain only.
-- Flights 8 and 10-15 have no crew assigned yet (useful for testing LEFT JOIN queries).
-- ---------------------------------------------------------
INSERT INTO flight_crew (flight_id, pilot_id, role) VALUES
    (1,  1, 'Captain'),
    (1,  6, 'First Officer'),
    (2,  3, 'Captain'),
    (2,  4, 'First Officer'),
    (3,  5, 'Captain'),
    (3,  8, 'First Officer'),
    (4,  7, 'Captain'),
    (4,  9, 'First Officer'),
    (5, 10, 'Captain'),
    (5, 12, 'First Officer'),
    (6,  2, 'Captain'),
    (6, 11, 'First Officer'),
    (7,  1, 'Captain'),
    (7,  4, 'First Officer'),
    (9,  3, 'Captain');

COMMIT;
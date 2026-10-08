-- ---------------------------------------------------------
-- SAMPLE DATA
-- ---------------------------------------------------------
INSERT INTO destination (airport_code, airport_name, city, country) VALUES
    ('LHR', 'Heathrow Airport',     'London',   'United Kingdom'),
    ('CDG', 'Charles de Gaulle',    'Paris',    'France'),
    ('JFK', 'John F. Kennedy Intl', 'New York', 'United States');

INSERT INTO aircraft (registration_number, model, capacity) VALUES
    ('G-EUPT', 'Airbus A320', 180),
    ('G-XWBA', 'Airbus A350', 331);

INSERT INTO pilot (licence_number, first_name, last_name, hire_date, phone_number, email) VALUES
    ('UK-10234', 'Sarah', 'Evans',  '2015-03-12', '07700 900111', 'sarah.evans@example.com'),
    ('UK-10987', 'James', 'Morgan', '2018-07-01', '07700 900222', 'james.morgan@example.com'),
    ('UK-11456', 'Priya', 'Patel',  '2020-01-20', '07700 900333', 'priya.patel@example.com');

INSERT INTO flight (flight_number, departure_time, arrival_time, origin_id, destination_id, aircraft_id) VALUES
    ('BA214', '2026-11-02 08:30:00', '2026-11-02 09:45:00', 1, 2, 1),
    ('BA330', '2026-11-02 14:00:00', '2026-11-02 21:10:00', 1, 3, 2);

INSERT INTO flight_crew (flight_id, pilot_id, role) VALUES
    (1, 1, 'Captain'),
    (1, 2, 'First Officer'),
    (2, 3, 'Captain'),
    (2, 2, 'First Officer');
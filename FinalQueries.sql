-- Drop tables if exists
DROP TABLE IF EXISTS booked_appointments;
DROP TABLE IF EXISTS doctors;

-- Table 1: Doctors
CREATE TABLE doctors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    speciality VARCHAR(100) NOT NULL,
    years_of_experience INTEGER NOT NULL CHECK (years_of_experience >= 0),
    consultation_fee DECIMAL(10, 2) NOT NULL CHECK (consultation_fee >= 0)
);

-- Table 2: Booked Appointments
CREATE TABLE booked_appointments (
    id SERIAL PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    doctor_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
    CHECK (status IN ('pending', 'confirmed', 'cancelled', 'completed'))
);

-- Insert sample doctors data
INSERT INTO doctors (name, speciality, years_of_experience, consultation_fee) VALUES
    ('Dr. Sarah Ahmed', 'Cardiologist', 15, 2500.00),
    ('Dr. Muhammad Ali', 'Cardiologist', 8, 2000.00),
    ('Dr. Fatima Khan', 'Dermatologist', 12, 1800.00),
    ('Dr. Hassan Raza', 'Pediatrician', 10, 1500.00),
    ('Dr. Ayesha Malik', 'Orthopedic', 20, 3000.00),
    ('Dr. Imran Sheikh', 'Neurologist', 18, 2800.00),
    ('Dr. Zainab Noor', 'Pediatrician', 5, 1200.00),
    ('Dr. Omar Farooq', 'Dermatologist', 7, 1600.00),
    ('Dr. Mariam Siddiqui', 'General Physician', 14, 1000.00),
    ('Dr. Bilal Anwar', 'Orthopedic', 9, 2200.00);

-- Insert sample appointments data
INSERT INTO booked_appointments (patient_name, doctor_id, reason, status) VALUES
    ('Ali Hassan', 1, 'Chest pain and irregular heartbeat', 'confirmed'),
    ('Sana Ahmed', 4, 'Child vaccination checkup', 'completed'),
    ('Kamran Iqbal', 5, 'Knee joint pain', 'pending'),
    ('Hira Waseem', 3, 'Skin allergy treatment', 'confirmed'),
    ('Farhan Malik', 6, 'Severe headaches', 'pending');

-- Create indexes for better query performance
CREATE INDEX idx_doctors_speciality ON doctors(speciality);
CREATE INDEX idx_appointments_doctor_id ON booked_appointments(doctor_id);
CREATE INDEX idx_appointments_status ON booked_appointments(status);

-- Verification queries
SELECT 'Doctors Table:' as info;
SELECT * FROM doctors ORDER BY id;

SELECT 'Booked Appointments Table:' as info;
SELECT * FROM booked_appointments ORDER BY id;

SELECT 'Doctors by Speciality:' as info;
SELECT speciality, COUNT(*) as doctor_count 
FROM doctors 
GROUP BY speciality 
ORDER BY doctor_count DESC;

ALTER TABLE booked_appointments 
ADD CONSTRAINT unique_doctor_time UNIQUE (doctor_id, appointment_time);
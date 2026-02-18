🩺 MedConnect: AI Medical ReceptionistMedConnect is an intelligent, agentic medical appointment system powered by LangGraph and Groq. 
It doesn't just process text; it understands intent, validates SQL queries, manages a PostgreSQL database, and prevents scheduling conflicts (like double-bookings) autonomously.

🚀 Features: 
Natural Language Understanding: Users can book appointments by doctor name instead of ID. The agent uses SQL subqueries to resolve names.
Intelligent Intent Classification: Automatically distinguishes between "Reading" (searching doctors/appointments) and "Writing" (booking/rescheduling).
Conflict Prevention: Uses a PostgreSQL UNIQUE constraint to ensure no doctor is double-booked for the same time slot.
Multi-Step Validation: Every SQL query generated is passed through a "Validator LLM" to ensure it adheres to the database schema before execution.
Graceful Error Handling: If a time slot is taken or data is missing, the agent engages in a conversation to collect the correct details rather than crashing.

🛠️ Technology Stack:
Component,Technology
Orchestration,LangGraph (Stateful Multi-Agent Framework)
LLM Engine,Groq (Llama-3 / GPT-OSS models)
Database,PostgreSQL
Language,Python 3.10+
Library,LangChain / Psycopg2

 Prerequisites: 
 PostgreSQL installed and running.
 Groq API Key (Get it at console.groq.com).
 Python 3.10+.
⚙️ Setup Instructions1. 
Database InitializationRun the following SQL to set up your tables and the critical double-booking protection:

SQLCREATE TABLE doctors (
    id SERIAL PRIMARY KEY,
    name TEXT,
    specialty TEXT,
    years_of_experience INT,
    consultation_fee INT
);

CREATE TABLE booked_appointments (
    id SERIAL PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    doctor_id INTEGER REFERENCES doctors(id),
    reason TEXT NOT NULL,
    appointment_time TIMESTAMP NOT NULL,
    UNIQUE (doctor_id, appointment_time) -- The anti-double-booking shield
);
2. Environment ConfigurationCreate a .env file in the root directory:PlaintextGROQ_API_KEY=your_actual_key_here
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
Note: Ensure .env is added to your .gitignore to prevent secret leaks!3. Install DependenciesBashpip install -r requirements.txt
🛡️ Security & ConstraintsPush Protection: 
The project is configured to avoid committing secrets.
SQL Injection Prevention: The agent utilizes structured LLM prompting and a validation node to ensure queries remain within the intended schema.
Write Protection: The "Read" node is hard-coded to reject any query that does not start with SELECT.

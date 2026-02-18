import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage 
from langchain_core.prompts import ChatPromptTemplate 
from logger_config import setup_logger

# Initialize logger
logger = setup_logger("Groq_Client")
load_dotenv()

def get_groq_llm():
    """
    Initialize and return the Groq LLM.
    Uses the openai gpt-oss-20b model (fast and capable)
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

        if not api_key:
            logger.error("GROQ_API_KEY not found in environment variables.")
            raise ValueError("GROQ_API_KEY not found in .env file")

        system_message = SystemMessage(content="""
        You are an SQL generator for a PostgreSQL database.
        CRITICAL RULES:
        - Return ONLY raw SQL
        - DO NOT include <think>, explanations, comments, or markdown
        - Output must start directly with SELECT / INSERT / UPDATE / DELETE                                      
        - You MUST only use the tables and columns that exist in the schema below.
        - If the user mentions a category (e.g., cardiologists), do NOT invent a table.
        - Instead, filter the doctors table using WHERE specialty ILIKE '%<category>%'.

        DATABASE SCHEMA:
        TABLE doctors(
            id SERIAL PRIMARY KEY,
            name TEXT,
            specialty TEXT,
            years_of_experience INT,
            consultation_fee INT
        );

        TABLE booked_appointments(
            id SERIAL PRIMARY KEY,
            patient_name VARCHAR(100) NOT NULL,
            doctor_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            appointment_time TIMESTAMP NOT NULL,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
            UNIQUE (doctor_id, appointment_time)
        );
        
        SPECIAL BEHAVIOR INSTRUCTIONS:
        1. BOOKING BY DOCTOR NAME: NEVER ask for a doctor_id. If a user provides a doctor's name, use a subquery to find their ID.
           Example: INSERT INTO booked_appointments (patient_name, doctor_id, reason, appointment_time) VALUES ('John Doe', (SELECT id FROM doctors WHERE name ILIKE '%Smith%' LIMIT 1), 'Checkup', '2026-02-25 10:00:00');
        2. EDITING APPOINTMENTS: If a user wants to edit/change/reschedule an appointment, use an UPDATE statement.
           Example: UPDATE booked_appointments SET appointment_time = '2026-02-26 14:00:00' WHERE patient_name ILIKE '%John Doe%';
           
        There is NO table named cardiologists, dermatologists, etc.
        """)
        
        base_llm = ChatGroq(
            api_key=api_key,
            model=model,
            temperature=0,  # Deterministic responses for SQL generation
            max_tokens=2000
        )

        prompt = ChatPromptTemplate.from_messages([
            system_message,
            ("human", "{input}") 
        ])
        
        logger.info(f"Groq LLM (Generator) initialized successfully using model: {model}")
        return base_llm, prompt

    except Exception as e:
        logger.error(f"Error initializing Groq LLM: {str(e)}")
        raise

def get_sql_validator_llm():
    """Initializes the SQL validator with error handling."""
    try:
        validator_prompt = ChatPromptTemplate.from_messages([
            ("system", """
        You are an expert PostgreSQL SQL validator. 
        Your job is to:

        1. Check if the SQL is valid for this schema.
        2. Ensure ONLY these columns are used (Subqueries using doctor name are allowed):

        TABLE doctors(
            id,
            name,
            specialty,
            years_of_experience,
            consultation_fee
        );

        TABLE booked_appointments(
            id,
            patient_name,
            doctor_id,
            reason,
            status,
            created_at,
            appointment_time
        );

        3. If any wrong column or table is found: FIX the SQL.
        4. NEVER change user intent. Allow SELECT, INSERT, UPDATE, and DELETE.
        5. ALWAYS return ONLY the corrected SQL. No explanations.

        If SQL is valid, return it unchanged.
    """),
            ("human", "{sql}")
        ])

        llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="openai/gpt-oss-20b",
            temperature=0
        )
        
        logger.info("SQL Validator LLM initialized successfully.")
        return validator_prompt | llm

    except Exception as e:
        logger.error(f"Error initializing SQL Validator LLM: {str(e)}")
        raise

def test_groq_connection():
    """Test basic Groq API connection"""
    try:
        base_llm, prompt = get_groq_llm()
        
        final_chain = prompt | base_llm
        # Simple test message
        response = final_chain.invoke("Say 'Hello, I am working!' in one sentence.")
        
        print("Groq API connection successful")
        print(f"✓ Model response: {response.content}")
        logger.info("Groq connection test successful.")
        
        return True
        
    except Exception as e:
        print(f"Groq API error: {e}")
        logger.error(f"Groq API connection test failed: {str(e)}")
        return False

def get_conversational_llm():
    """Initializes the conversational assistant with error handling."""
    try:
        system = SystemMessage(content="""
            You are MedConnect, a professional medical assistant.

            OPERATIONAL GUIDELINES:
            1. MISSING INFO: If the user hasn't provided a Patient Name, Doctor Name, Time, or Reason, do not attempt to finalize a booking. Instead, ask for the missing details.
            2. DATABASE ERRORS: If the 'Database Result' starts with 'Error:', explain the problem to the user in plain language (e.g., "That slot is already taken").
            3. SECURITY BLOCKS: If the result is 'Unauthorized operation', apologize and ask the user to provide booking details like name and time more clearly.

            CRITICAL RULES:
            - Respond ONLY with the final answer to the user.
            - NEVER reveal internal reasoning, thoughts, or <think> blocks.
            - NEVER use placeholders like [patient_name].
            - Be concise and professional.
""")
        
        llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            temperature=0.3,
        )

        logger.info("Conversational LLM initialized successfully.")
        return llm, system

    except Exception as e:
        logger.error(f"Error initializing Conversational LLM: {str(e)}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Groq API Connection")
    print("=" * 60)
    test_groq_connection()






# import os
# from dotenv import load_dotenv
# from langchain_groq import ChatGroq
# from langchain_core.messages import SystemMessage 
# from langchain_core.prompts import ChatPromptTemplate 
# from logger_config import setup_logger

# logger = setup_logger("Groq_Client")
# load_dotenv()

# def get_groq_llm():
#     """
#     Initialize and return the Groq LLM.
#     Uses the openai gpt-oss-20b model (fast and capable)
#     """
#     api_key = os.getenv("GROQ_API_KEY")
#     model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

#     system_message = SystemMessage(content="""
#     You are an SQL generator for a PostgreSQL database.
#     CRITICAL RULES:
#     - Return ONLY raw SQL
#     - DO NOT include <think>, explanations, comments, or markdown
#     - Output must start directly with SELECT / INSERT / UPDATE / DELETE                            
#     - You MUST only use the tables and columns that exist in the schema below.
#     - If the user mentions a category (e.g., cardiologists), do NOT invent a table.
#     - Instead, filter the doctors table using WHERE specialty ILIKE '%<category>%'.

#     DATABASE SCHEMA:
#     TABLE doctors(
#         id SERIAL PRIMARY KEY,
#         name TEXT,
#         specialty TEXT,
#         years_of_experience INT,
#         consultation_fee INT
#     );

#     TABLE booked_appointments(
#         id SERIAL PRIMARY KEY,
#         patient_name VARCHAR(100) NOT NULL,
#         doctor_id INTEGER NOT NULL,
#         reason TEXT NOT NULL,
#         status VARCHAR(20) NOT NULL DEFAULT 'pending',
#         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#         appointment_time TIMESTAMP NOT NULL,
#         FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
#         CHECK (status IN ('pending', 'confirmed', 'cancelled', 'completed'))
#     );
    
#     There is NO table named cardiologists, dermatologists, etc.
#     """)
    
#     if not api_key:
#         raise ValueError("GROQ_API_KEY not found in .env file")
    
#     base_llm = ChatGroq(
#         api_key=api_key,
#         model=model,
#         temperature=0,  # Deterministic responses for SQL generation
#         max_tokens=2000
#     )

#     prompt = ChatPromptTemplate.from_messages([
#         system_message,
#         ("human", "{input}") ])
    
#     return  base_llm, prompt

# def get_sql_validator_llm():
#     validator_prompt = ChatPromptTemplate.from_messages([
#         ("system", """
#     You are an expert PostgreSQL SQL validator. 
#     Your job is to:

#     1. Check if the SQL is valid for this schema.
#     2. Ensure ONLY these columns are used:

#     TABLE doctors(
#         id,
#         name,
#         specialty,
#         years_of_experience,
#         consultation_fee
#     );

#     TABLE booked_appointments(
#         id,
#         patient_name,
#         doctor_id,
#         reason,
#         status,
#         created_at,
#         appointment_time
#     );

#     3. If any wrong column or table is found: FIX the SQL.
#     4. NEVER change user intent.
#     5. ALWAYS return ONLY the corrected SQL. No explanations.

#     If SQL is valid, return it unchanged.
# """),
#         ("human", "{sql}")
#     ])

#     return validator_prompt | ChatGroq(
#         api_key=os.getenv("GROQ_API_KEY"),
#         model="openai/gpt-oss-20b",
#         temperature=0
#     )

# def test_groq_connection():
#     """Test basic Groq API connection"""
#     try:
#         base_llm, prompt = get_groq_llm()
        
#         final_chain = prompt | base_llm
#         # Simple test message
#         response = final_chain.invoke("Say 'Hello, I am working!' in one sentence.")
        
#         print("✓ Groq API connection successful")
#         print(f"✓ Model response: {response.content}")
        
#         return True
        
#     except Exception as e:
#         print(f"✗ Groq API error: {e}")
#         return False

# def get_conversational_llm():
#     system = SystemMessage(content="""
#         You are MedConnect, a medical assistant.

#         CRITICAL RULES:
#         - NEVER reveal your thoughts, reasoning, or analysis
#         - NEVER say phrases like "I think", "I need to", "Let me"
#         - NEVER explain decision making
#         - Respond ONLY with the final answer to the user
#         - Be concise and professional
#         - NEVER reveal thoughts, reasoning, or analysis
#         - NEVER include <think> blocks
#         - Respond ONLY with the final answer to the user
#     """)
#     llm = ChatGroq(
#         api_key=os.getenv("GROQ_API_KEY"),
#         model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
#         temperature=0.3,
#     )

#     return llm, system

# if __name__ == "__main__":
#     print("=" * 60)
#     print("Testing Groq API Connection")
#     print("=" * 60)
#     test_groq_connection()




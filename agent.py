import psycopg2
from psycopg2 import errors
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from mcp_setup import DB_CONFIG
from groq_client import get_groq_llm, get_sql_validator_llm, get_conversational_llm
from logger_config import setup_logger

logger = setup_logger("Agent_Orchestrator")

# --- 1. Define Agent State ---
class AgentState(TypedDict):
    user_input: str
    intent: Literal["read", "write", "unknown"]
    generated_sql: str
    is_valid: bool
    db_result: str
    final_response: str

# --- 2. Execution Helper ---
def execute_query_safe(sql: str, fetch: bool = True):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(sql)
        if fetch:
            res = str(cur.fetchall())
            logger.info("READ operation successful.")
            return res
        else:
            rows_affected = cur.rowcount
            conn.commit()
            logger.info(f"WRITE operation committed. Rows affected: {rows_affected}")
            if rows_affected == 0 and "UPDATE" in sql.upper():
                return "Error: Could not find an appointment for that user to update."
            return "Success."
    except errors.UniqueViolation:
        if conn: conn.rollback()
        logger.warning("Double booking attempt blocked by database constraint.")
        return "Error: This day and time is already filled. Tell the user to book another slot."
    except psycopg2.Error as e:
        if conn: conn.rollback()
        error_log = f"Postgres Error: {e.pgerror if hasattr(e, 'pgerror') else str(e)}"
        logger.error(error_log)
        return error_log
    except Exception as e:
        if conn: conn.rollback()
        logger.critical(f"Unexpected DB Failure: {str(e)}")
        return "System failure."
    finally:
        if conn: conn.close()

# --- 3. Define Nodes ---

def intent_classifier(state: AgentState):
    user_text = state["user_input"].lower()
    
    write_keywords = ["book", "appointment", "schedule", "edit", "change", "reschedule", "update", "patient", "time:", "reason:"]
    
    if any(k in user_text for k in write_keywords):
        intent = "write"
    else:
        intent = "read"
        
    logger.info(f"Classified intent: {intent}")
    return {"intent": intent}

def sql_generator_node(state: AgentState):
    try:
        # If intent is write, check if we have the basics in the user_input
        # This prevents the LLM from hallucinating <placeholders>
        if state["intent"] == "write":
            user_text = state["user_input"].lower()
            # Simple check for Name, Time/Date, and Reason
            # You can make this more complex or use an LLM call
            if not any(word in user_text for word in ["at", "on", "2026", "pm", "am"]):
                 logger.info("Missing time info. Skipping SQL generation.")
                 return {"generated_sql": "MISSING_INFO", "is_valid": False}

        llm, prompt = get_groq_llm()
        response = (prompt | llm).invoke({"input": state["user_input"]})
        sql = response.content.strip().replace("```sql", "").replace("```", "")
        logger.info(f"Generated SQL: {sql}")
        return {"generated_sql": sql}
    except Exception as e:
        logger.error(f"SQL Generation Node failed: {str(e)}")
        return {"generated_sql": "Error", "is_valid": False}

def sql_validator_node(state: AgentState):
    """New Node: Validates and fixes SQL before execution"""
    try:
        validator_chain = get_sql_validator_llm()
        response = validator_chain.invoke({"sql": state["generated_sql"]})
        validated_sql = response.content.strip().replace("```sql", "").replace("```", "")
        
        # Simple check: If the validator returns an empty string or non-SQL text
        is_valid = any(keyword in validated_sql.upper() for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE"])
        
        logger.info(f"SQL Validated. Corrected SQL: {validated_sql}")
        return {"generated_sql": validated_sql, "is_valid": is_valid}
    except Exception as e:
        logger.error(f"SQL Validation Node failed: {str(e)}")
        return {"is_valid": False}

def write_executor_node(state: AgentState):
    sql = state["generated_sql"]
    if not any(sql.upper().startswith(cmd) for cmd in ["INSERT", "UPDATE", "DELETE"]):
        logger.warning(f"Security Block: Non-Write query in WRITE node: {sql}")
        return {"db_result": "Unauthorized operation. Only writes are allowed here."}
    return {"db_result": execute_query_safe(sql, fetch=False)}

def read_executor_node(state: AgentState):
    sql = state["generated_sql"]
    if not sql.upper().startswith("SELECT"):
        logger.warning(f"Security Block: Non-SELECT query in READ node: {sql}")
        return {"db_result": "Unauthorized operation."}
    return {"db_result": execute_query_safe(sql, fetch=True)}

def response_generator_node(state: AgentState):
    try:
        llm, system_msg = get_conversational_llm()
        if not state.get("is_valid", True):
            db_context = "The generated SQL was invalid and could not be executed."
        else:
            db_context = state['db_result']

        prompt = f"User: {state['user_input']}\nDatabase Result: {db_context}"
        res = llm.invoke([system_msg, HumanMessage(content=prompt)])
        return {"final_response": res.content}
    except Exception as e:
        logger.error(f"Final response node failed: {str(e)}")
        return {"final_response": "I apologize, but I encountered an internal error."}

# --- 4. Build the Graph ---

workflow = StateGraph(AgentState)

# Add all nodes
workflow.add_node("classify", intent_classifier)
workflow.add_node("generate", sql_generator_node)
workflow.add_node("validate", sql_validator_node) 
workflow.add_node("read", read_executor_node)
workflow.add_node("write", write_executor_node)
workflow.add_node("respond", response_generator_node)

# Entry and linear flow to validation
workflow.set_entry_point("classify")
workflow.add_edge("classify", "generate")
workflow.add_edge("generate", "validate") 

# Conditional Router after Validation
def router(state: AgentState):
    # If the generator flagged missing info, go straight to the conversational responder
    if state.get("generated_sql") == "MISSING_INFO" or not state.get("is_valid", False):
        logger.warning("Incomplete data or validation failed. Routing to response.")
        return "respond"
    
    return "read" if state["intent"] == "read" else "write"

workflow.add_conditional_edges(
    "validate", 
    router, 
    {
        "read": "read", 
        "write": "write", 
        "respond": "respond"
    }
)

workflow.add_edge("read", "respond")
workflow.add_edge("write", "respond")
workflow.add_edge("respond", END)

app = workflow.compile()

if __name__ == "__main__":
    logger.info("--- Agent Session Started ---")

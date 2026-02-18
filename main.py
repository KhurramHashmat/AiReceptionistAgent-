import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from agent import app as agent_graph  
from logger_config import setup_logger

logger = setup_logger("FastAPI_Backend")

app = FastAPI(title="MedConnect AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data model for the request
class ChatRequest(BaseModel):
    user_input: str
    chat_history: Optional[List[dict]] = []

# Data model for the response
class ChatResponse(BaseModel):
    final_response: str
    intent: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint to interact with the LangGraph Healthcare Agent.
    """
    try:
        logger.info(f"Received request: {request.user_input}")
        
        # Invoke the LangGraph agent
        # We pass the initial state required by your AgentState TypedDict
        inputs = {
            "messages": request.chat_history,
            "user_input": request.user_input,
            "intent": "unknown",
            "generated_sql": "",
            "is_valid": False,
            "db_result": "",
            "final_response": ""
        }
        
        result = agent_graph.invoke(inputs)
        
        logger.info(f"Agent successfully processed request. Intent: {result['intent']}")
        
        return ChatResponse(
            final_response=result["final_response"],
            intent=result["intent"]
        )

    except Exception as e:
        logger.error(f"Error in chat_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
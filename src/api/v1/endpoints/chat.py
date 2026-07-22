from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Literal
from openai import OpenAI
from src.core.config import settings
from src.schemas.chat import ChatRequest

router = APIRouter()

class RouteDecision(BaseModel):
    destination: Literal["rag_pipeline", "refuse"] = Field(
        description="Choose 'rag_pipeline' for hardware, tech support, or engineering specs. Choose 'refuse' for general chat, math, or unrelated prompts."
    )
    reason: str

@router.post("/stream", status_code=status.HTTP_200_OK)
async def process_chat(payload: ChatRequest):
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Evaluate context domain dynamically
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a specialized router for an industrial hardware support system. Categorize if the question concerns technology, engineering specs, or troubleshooting."
                },
                {"role": "user", "content": payload.message}
            ],
            response_format=RouteDecision,
        )
        
        decision = completion.choices[0].message.parsed
        
        # Branch execution based on routing target
        if decision.destination == "refuse":
            return {
                "routing": "refuse",
                "response": "I am an AI assistant optimized specifically for technical machinery manuals and customer support records. I cannot process general questions outside of this domain."
            }
            
        return {
            "routing": "rag_pipeline",
            "response": f"Query approved for processing. (Simulated path for query: '{payload.message}')"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
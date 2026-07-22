# src/services/gemini_service.py
import httpx

# FIX: Changed endpoint to /api/chat for better model compatibility
OLLAMA_URL = "http://localhost:11434/api/chat"
# Change this line near the top of the file:
MODEL_NAME = "llama3.1:latest"  # Ensure this matches the exact name from 'ollama list'

async def generate_answer(user_query: str, context: str) -> str:
    system_instruction = (
        "You are an expert engineering assistant specializing in CNC machinery and hardware manufacturing.\n"
        "Your task is to answer the user's question accurately using ONLY the provided technical context snippets.\n"
        "Strict Guidelines:\n"
        "1. Respond naturally in the SAME language the user used to ask the question.\n"
        "2. Keep your answer highly factual and concrete based on the context.\n"
        "3. If the context does not contain enough information to answer, state clearly that you do not have that data."
    )
    
    # Structure payload using standard chat roles
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Technical Context Data:\n{context}\n\nUser Question: {user_query}"}
        ],
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Extract response text from chat structure
            return result.get("message", {}).get("content", "").strip()
            
    except httpx.HTTPStatusError as e:
        raise Exception(f"Ollama error: Server responded with status {e.response.status_code}. Verify that model '{MODEL_NAME}' is pulled.")
    except httpx.RequestError as e:
        raise Exception(f"Failed to reach local Ollama instance: {str(e)}. Ensure Ollama is running.")
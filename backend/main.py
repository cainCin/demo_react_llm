"""
FastAPI backend for chatbox application with LLM integration
"""
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI, AzureOpenAI

# Load environment variables
load_dotenv()

app = FastAPI(title="Chatbox API", version="1.0.0")

# CORS middleware to allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client (supports both standard OpenAI and Azure OpenAI)
openai_api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

openai_client = None
use_azure = False

if azure_endpoint and openai_api_key:
    # Use Azure OpenAI
    use_azure = True
    
    # Initialize Azure OpenAI client using AzureOpenAI class
    # Azure OpenAI requires: api_key, api_version, and azure_endpoint
    openai_client = AzureOpenAI(
        api_key=openai_api_key,
        api_version=azure_api_version,
        azure_endpoint=azure_endpoint.rstrip('/'),
    )
    print(f"✅ Initialized Azure OpenAI client")
    print(f"   Endpoint: {azure_endpoint}")
    print(f"   Deployment: {azure_deployment or 'Not specified (will use model parameter)'}")
    print(f"   API Version: {azure_api_version}")
elif openai_api_key:
    # Use standard OpenAI
    openai_client = OpenAI(api_key=openai_api_key)
    print("✅ Initialized standard OpenAI client")
else:
    print("⚠️  No OpenAI API key configured")


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None  # Will use default based on provider


class ChatResponse(BaseModel):
    message: str
    model: str


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Chatbox API is running"}


@app.get("/api/health")
async def health():
    """Health check endpoint accessible through proxy"""
    return {"status": "ok", "message": "Chatbox API is running"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint that sends messages to LLM API and returns response
    """
    if not openai_client:
        error_msg = "OpenAI API key not configured."
        if not azure_endpoint:
            error_msg += " Please set OPENAI_API_KEY in .env file"
        else:
            error_msg += " Please set OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in .env file"
        raise HTTPException(status_code=500, detail=error_msg)
    
    try:
        # Convert messages to OpenAI format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Determine model/deployment to use
        model_to_use = request.model
        if use_azure:
            # For Azure OpenAI, use deployment name if provided, otherwise use model parameter
            if azure_deployment:
                # Use deployment name (required for Azure OpenAI)
                model_to_use = azure_deployment
            elif not model_to_use:
                # Default Azure model name (Azure uses different naming)
                model_to_use = "gpt-35-turbo"
        elif not model_to_use:
            # Standard OpenAI default
            model_to_use = "gpt-3.5-turbo"
        
        # Prepare API call parameters
        api_params = {
            "model": model_to_use,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        # Make the API call
        response = openai_client.chat.completions.create(**api_params)
        
        # Extract the assistant's message
        assistant_message = response.choices[0].message.content
        
        return ChatResponse(
            message=assistant_message,
            model=model_to_use
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calling LLM API: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


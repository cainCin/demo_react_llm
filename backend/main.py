"""
FastAPI backend for chatbox application with LLM integration
"""
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI, AzureOpenAI
from rag_system import RAGSystem
from config import (
    RAG_ENABLED, LLM_TEMPERATURE, LLM_MAX_TOKENS, MAX_FILE_SIZE,
    EMBEDDING_MODEL, RAG_TOP_K, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_DIM,
    LLM_TIMEOUT
)

# Load environment variables
load_dotenv()

app = FastAPI(title="Chatbox API", version="1.0.0")

# CORS middleware to allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
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
    try:
        openai_client = AzureOpenAI(
            api_key=openai_api_key,
            api_version=azure_api_version,
            azure_endpoint=azure_endpoint.rstrip('/'),
            timeout=LLM_TIMEOUT,
        )
        print(f"✅ Initialized Azure OpenAI client")
        print(f"   Endpoint: {azure_endpoint}")
        print(f"   Deployment: {azure_deployment or 'Not specified (using model parameter)'}")
        print(f"   API Version: {azure_api_version}")
        print(f"   Timeout: {LLM_TIMEOUT}s")
        
        # Test connection with a simple API call (optional, may fail if models.list is not available)
        try:
            print("   Testing connection...")
            # Try to list models - this is a lightweight operation
            test_response = openai_client.models.list()
            print("   ✅ Connection test successful")
        except Exception as test_error:
            # Connection test failure is not critical - the client is still initialized
            # It might fail due to permissions or API version differences
            print(f"   ⚠️  Connection test skipped (this is usually fine): {test_error}")
    except Exception as init_error:
        print(f"❌ Failed to initialize Azure OpenAI client: {init_error}")
        openai_client = None
elif openai_api_key:
    # Use standard OpenAI
    try:
        openai_client = OpenAI(api_key=openai_api_key, timeout=LLM_TIMEOUT)
        print("✅ Initialized standard OpenAI client")
        print(f"   Timeout: {LLM_TIMEOUT}s")
    except Exception as init_error:
        print(f"❌ Failed to initialize OpenAI client: {init_error}")
        openai_client = None
else:
    print("⚠️  No OpenAI API key configured")

# Initialize RAG system (optional, can be disabled)
rag_system = None

if RAG_ENABLED and openai_client:
    try:
        # Determine embedding model based on provider
        embedding_model = EMBEDDING_MODEL
        if use_azure:
            # Azure OpenAI uses different model names or deployment names
            embedding_model = os.getenv("AZURE_EMBEDDING_MODEL", EMBEDDING_MODEL)
            # If using deployment name for embeddings
            azure_embedding_deployment = os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME")
            if azure_embedding_deployment:
                embedding_model = azure_embedding_deployment
        
        rag_system = RAGSystem(openai_client, embedding_model=embedding_model, use_azure=use_azure)
        print("✅ RAG system initialized")
        print(f"   Chunk size: {CHUNK_SIZE}, Overlap: {CHUNK_OVERLAP}")
        print(f"   Embedding model: {embedding_model}, Dimension: {EMBEDDING_DIM}")
        print(f"   Top-K retrieval: {RAG_TOP_K}")
    except Exception as e:
        print(f"⚠️  Failed to initialize RAG system: {e}")
        print("   Continuing without RAG (files will still be processed)")
        rag_system = None
else:
    if not RAG_ENABLED:
        print("ℹ️  RAG system disabled (set RAG_ENABLED=true to enable)")
    else:
        print("ℹ️  RAG system not initialized (OpenAI client required)")


class Message(BaseModel):
    role: str
    content: str
    attachments: Optional[List[dict]] = None  # File attachments info


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
    return {
        "status": "ok",
        "message": "Chatbox API is running",
        "rag_enabled": rag_system is not None
    }


@app.get("/health")
async def health_direct():
    """Health check endpoint (direct access)"""
    return {
        "status": "ok",
        "message": "Chatbox API is running",
        "rag_enabled": rag_system is not None
    }


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extract text content from uploaded file based on file type
    """
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Text files
    if file_ext in ['txt', 'md', 'json', 'csv', 'log', 'py', 'js', 'html', 'css', 'xml', 'yaml', 'yml']:
        try:
            # Try UTF-8 first
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1
                return file_content.decode('latin-1')
            except:
                return f"[Unable to decode file: {filename}]"
    
    # For other file types, return a placeholder
    return f"[File: {filename} - Content extraction not supported for .{file_ext} files. Please convert to text format.]"


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a file, returning its text content
    If RAG is enabled, also stores the document in the RAG system
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Check file size
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.1f}MB."
            )
        
        # Extract text content
        text_content = extract_text_from_file(file_content, file.filename)
        
        # Store in RAG system if enabled
        document_id = None
        if rag_system:
            try:
                document_id = rag_system.store_document(file.filename, text_content)
                print(f"✅ Document stored in RAG: {file.filename}")
            except Exception as e:
                print(f"⚠️  Failed to store document in RAG: {e}")
                # Continue without RAG storage
        
        return {
            "filename": file.filename,
            "size": len(file_content),
            "content": text_content,
            "content_type": file.content_type,
            "document_id": document_id,
            "rag_stored": document_id is not None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@app.get("/api/documents")
async def list_documents():
    """List all stored documents (RAG system only)"""
    if not rag_system:
        raise HTTPException(status_code=400, detail="RAG system is not enabled")
    
    from database import Document
    from sqlalchemy.orm import Session
    
    db: Session = rag_system.db_manager.get_session()
    try:
        documents = db.query(Document).order_by(Document.created_at.desc()).all()
        return {
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "chunk_count": doc.chunk_count,
                    "created_at": doc.created_at.isoformat()
                }
                for doc in documents
            ]
        }
    finally:
        db.close()


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks (RAG system only)"""
    if not rag_system:
        raise HTTPException(status_code=400, detail="RAG system is not enabled")
    
    try:
        rag_system.delete_document(document_id)
        return {"status": "ok", "message": f"Document {document_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@app.delete("/api/documents")
async def clean_all_documents():
    """Clean all documents from both databases (RAG system only)"""
    if not rag_system:
        raise HTTPException(status_code=400, detail="RAG system is not enabled")
    
    try:
        rag_system.clean_all_databases()
        return {"status": "ok", "message": "All documents cleaned from both databases"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning databases: {str(e)}")


@app.get("/api/documents/sync")
async def check_synchronization():
    """Check if PostgreSQL and Milvus databases are synchronized (RAG system only)"""
    if not rag_system:
        raise HTTPException(status_code=400, detail="RAG system is not enabled")
    
    try:
        # Use DatabaseManager's verify method
        sync_status = rag_system.db_manager.verify()
        status_code = 200 if sync_status["synchronized"] else 207  # 207 Multi-Status
        return sync_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking synchronization: {str(e)}")


@app.post("/api/documents/resync")
async def resync_databases():
    """Resynchronize databases by ensuring all PostgreSQL chunks exist in Milvus (RAG system only)"""
    if not rag_system:
        raise HTTPException(status_code=400, detail="RAG system is not enabled")
    
    try:
        resync_result = rag_system.resync_databases()
        status_code = 200 if resync_result["success"] else 207
        return resync_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resynchronizing databases: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint that sends messages to LLM API and returns response
    Uses RAG system to retrieve relevant context if enabled
    """
    if not openai_client:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY in .env file"
        )
    
    try:
        # Get the last user message for RAG retrieval
        last_user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                last_user_message = msg
                break
        
        # Retrieve relevant context from RAG if enabled
        rag_context = ""
        if rag_system and last_user_message:
            try:
                # Search for similar chunks
                query_text = last_user_message.content
                if last_user_message.attachments:
                    # Include attachment content in query
                    for attachment in last_user_message.attachments:
                        query_text += " " + attachment.get('content', '')[:500]  # Limit query size
                
                similar_chunks = rag_system.search_similar(query_text, top_k=RAG_TOP_K)
                
                if similar_chunks:
                    # Build context from retrieved chunks
                    context_parts = ["[Relevant context from documents:]"]
                    for chunk in similar_chunks:
                        context_parts.append(f"\n---\n{chunk['text']}")
                    rag_context = "\n".join(context_parts)
                    print(f"✅ Retrieved {len(similar_chunks)} relevant chunks from RAG")
            except Exception as e:
                print(f"⚠️  RAG retrieval error: {e}")
                # Continue without RAG context
        
        # Convert messages to OpenAI format, including file attachments and RAG context
        messages = []
        for msg in request.messages:
            content_parts = [msg.content]
            
            # Add RAG context to the last user message
            if msg.role == "user" and msg == last_user_message and rag_context:
                content_parts.append(f"\n\n{rag_context}")
            
            # Add file attachments to the message content
            if msg.attachments:
                for attachment in msg.attachments:
                    filename = attachment.get('filename', 'file')
                    file_content = attachment.get('content', '')
                    if file_content:
                        content_parts.append(f"\n\n[Attachment: {filename}]\n{file_content}")
            
            # Combine all content parts
            full_content = "\n".join(content_parts)
            messages.append({"role": msg.role, "content": full_content})
        
        # Determine model/deployment to use
        model_to_use = request.model
        if use_azure:
            # For Azure OpenAI, use deployment name if provided, otherwise use model parameter
            if azure_deployment:
                model_to_use = azure_deployment
            elif not model_to_use:
                model_to_use = "gpt-35-turbo"  # Azure naming convention
        elif not model_to_use:
            model_to_use = "gpt-3.5-turbo"  # Standard OpenAI default
        
        # Prepare API call parameters
        api_params = {
            "model": model_to_use,
            "messages": messages,
            "temperature": LLM_TEMPERATURE,
            "max_tokens": LLM_MAX_TOKENS
        }
        
        # Make the API call with timeout handling
        try:
            response = openai_client.chat.completions.create(**api_params)
        except Exception as api_error:
            error_str = str(api_error)
            # Provide more specific error messages
            if "timeout" in error_str.lower() or "timed out" in error_str.lower():
                raise HTTPException(
                    status_code=504,
                    detail=f"Request to Azure OpenAI timed out after {LLM_TIMEOUT}s. The service may be slow or unavailable. Please try again."
                )
            elif "connection" in error_str.lower() or "network" in error_str.lower():
                raise HTTPException(
                    status_code=503,
                    detail=f"Cannot connect to Azure OpenAI service. Please check your network connection and endpoint configuration."
                )
            elif "authentication" in error_str.lower() or "unauthorized" in error_str.lower() or "401" in error_str:
                raise HTTPException(
                    status_code=401,
                    detail="Azure OpenAI authentication failed. Please check your API key and endpoint configuration."
                )
            elif "rate limit" in error_str.lower() or "429" in error_str:
                raise HTTPException(
                    status_code=429,
                    detail="Azure OpenAI rate limit exceeded. Please try again later."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error calling Azure OpenAI API: {error_str}"
                )
        
        # Extract the assistant's message
        assistant_message = response.choices[0].message.content
        
        return ChatResponse(
            message=assistant_message,
            model=model_to_use
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


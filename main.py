from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import io
import asyncio
from typing import Optional
import uvicorn

from services.rag_service import RAGService
from services.tts_service import TTSService
from services.stt_service import STTService
from config.settings import get_settings

# Initialize FastAPI app
app = FastAPI(
    title="AgentX AI RAG System",
    description="RAG system with voice capabilities for HR data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
settings = get_settings()
rag_service = RAGService()
tts_service = TTSService()
stt_service = STTService()

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Pydantic models
class QueryRequest(BaseModel):
    question: str
    use_voice: Optional[bool] = False

class QueryResponse(BaseModel):
    answer: str
    sources: list
    audio_url: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG system on startup"""
    await rag_service.initialize()
    print("RAG system initialized successfully")

@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse('frontend/index.html')

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the RAG system with text input"""
    try:
        # Get answer from RAG system
        result = await rag_service.query(request.question)
        
        response = QueryResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
        
        # Always enable TTS for bot responses
        try:
            audio_data = await tts_service.text_to_speech(result["answer"])
            # Save audio file temporarily
            audio_filename = f"response_{hash(result['answer']) % 10000}.mp3"
            audio_path = f"frontend/audio/{audio_filename}"
            
            # Create audio directory if it doesn't exist
            os.makedirs("frontend/audio", exist_ok=True)
            
            with open(audio_path, "wb") as f:
                f.write(audio_data)
            
            response.audio_url = f"/static/audio/{audio_filename}"
        except Exception as e:
            print(f"TTS Error: {e}")
            # Continue without audio if TTS fails
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice-query")
async def query_voice(audio_file: UploadFile = File(...)):
    """Query the RAG system with voice input - with TTS response"""
    try:
        # Convert audio to text
        audio_data = await audio_file.read()
        question = await stt_service.speech_to_text(audio_data)
        
        # Get answer from RAG system
        result = await rag_service.query(question)
        
        # Generate TTS for voice response
        audio_response = None
        try:
            audio_data = await tts_service.text_to_speech(result["answer"])
            audio_filename = f"voice_response_{hash(result['answer']) % 10000}.mp3"
            audio_path = f"frontend/audio/{audio_filename}"
            
            os.makedirs("frontend/audio", exist_ok=True)
            
            with open(audio_path, "wb") as f:
                f.write(audio_data)
            
            audio_response = f"/static/audio/{audio_filename}"
        except Exception as e:
            print(f"TTS Error in voice query: {e}")
        
        return {
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"],
            "audio_url": audio_response
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a new document"""
    try:
        content = await file.read()
        result = await rag_service.add_document(content.decode('utf-8'), file.filename)
        return {"message": "Document uploaded successfully", "document_id": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    """List all documents in the system"""
    try:
        documents = await rag_service.list_documents()
        return {"documents": documents}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )